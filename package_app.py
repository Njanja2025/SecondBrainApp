#!/usr/bin/env python3
import os
import sys
import shutil
import json
import logging
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
import platform
import tempfile
import smtplib
from email.message import EmailMessage
import requests

# --- CONFIGURATION ---
CODE_SIGN_IDENTITY = os.environ.get('CODE_SIGN_IDENTITY')  # e.g., 'Developer ID Application: ...'
APPLE_ID = os.environ.get('APPLE_ID')
APPLE_TEAM_ID = os.environ.get('APPLE_TEAM_ID')
APPLE_APP_SPECIFIC_PASSWORD = os.environ.get('APPLE_APP_SPECIFIC_PASSWORD')
NOTARIZE = bool(os.environ.get('NOTARIZE', '0') == '1')
DEPLOY_TARGET = os.environ.get('DEPLOY_TARGET')  # e.g., 's3://bucket/path' or 'scp:user@host:path'
FTP_TARGET = os.environ.get('FTP_TARGET')  # e.g., 'ftp://user:pass@host/path/'
GDRIVE_FOLDER_ID = os.environ.get('GDRIVE_FOLDER_ID')  # Google Drive folder ID
DASHBOARD_USER = os.environ.get('DASHBOARD_USER')
DASHBOARD_PASS = os.environ.get('DASHBOARD_PASS')
EMAIL_NOTIFY = os.environ.get('EMAIL_NOTIFY')  # recipient email
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_FROM = os.environ.get('TWILIO_FROM')
TWILIO_TO = os.environ.get('TWILIO_TO')
TEAMS_WEBHOOK_URL = os.environ.get('TEAMS_WEBHOOK_URL')
ARTIFACT_RETENTION = int(os.environ.get('ARTIFACT_RETENTION', '5'))  # Keep latest N builds
CDN_MIRROR_CMD = os.environ.get('CDN_MIRROR_CMD')  # e.g., 'aws s3 cp ... && aws cloudfront create-invalidation ...'
ENCRYPT_ARTIFACTS = bool(os.environ.get('ENCRYPT_ARTIFACTS', '0') == '1')
ENCRYPTION_PASSWORD = os.environ.get('ENCRYPTION_PASSWORD')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('package.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AppPackager:
    def __init__(self):
        self.app_name = "SecondBrain"
        self.version = "2025"
        self.build_dir = Path("build")
        self.app_bundle = self.build_dir / f"{self.app_name}.app"
        self.resources_dir = Path("resources")
        self.backup_dir = Path("backups")
        self.dist_dir = self.build_dir / "dist"
        
        # Create required directories
        self.build_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        # Initialize manifest
        self.manifest = {
            "app_name": self.app_name,
            "version": self.version,
            "build_date": datetime.now().isoformat(),
            "build_env": platform.platform(),
            "python_version": platform.python_version(),
            "code_signed": False,
            "notarized": False,
            "tested": False,
            "deployed": False,
            "files": []
        }

    def create_backup(self):
        """Create a backup of the current app bundle"""
        if self.app_bundle.exists():
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_name
            shutil.copytree(self.app_bundle, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        return None

    def calculate_checksums(self):
        """Calculate checksums for all files in the app bundle"""
        logger.info("Calculating checksums...")
        for root, _, files in os.walk(self.app_bundle):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        checksum = hashlib.sha256(f.read()).hexdigest()
                        rel_path = file_path.relative_to(self.app_bundle)
                        self.manifest["files"].append({
                            "path": str(rel_path),
                            "checksum": checksum,
                            "size": file_path.stat().st_size
                        })

    def code_sign(self):
        if not CODE_SIGN_IDENTITY:
            logger.info("No code signing identity provided. Skipping code signing.")
            return False
        logger.info(f"Code signing .app with identity: {CODE_SIGN_IDENTITY}")
        try:
            subprocess.run([
                'codesign', '--deep', '--force', '--verify', '--verbose',
                '--sign', CODE_SIGN_IDENTITY,
                str(self.app_bundle)
            ], check=True, capture_output=True)
            self.manifest["code_signed"] = True
            logger.info("Code signing successful.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Code signing failed: {e.stderr.decode()}")
            return False

    def create_dmg(self):
        """Create a DMG file from the app bundle"""
        logger.info("Creating DMG...")
        dmg_path = self.dist_dir / f"{self.app_name}-{self.version}.dmg"
        try:
            subprocess.run([
                'hdiutil', 'create',
                '-volname', f"{self.app_name}-{self.version}",
                '-srcfolder', str(self.app_bundle),
                '-ov', '-format', 'UDZO',
                str(dmg_path)
            ], check=True, capture_output=True)
            logger.info(f"Created DMG at {dmg_path}")
            return dmg_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create DMG: {e.stderr.decode()}")
            raise

    def code_sign_dmg(self, dmg_path):
        if not CODE_SIGN_IDENTITY:
            logger.info("No code signing identity provided for DMG. Skipping.")
            return False
        logger.info(f"Code signing DMG with identity: {CODE_SIGN_IDENTITY}")
        try:
            subprocess.run([
                'codesign', '--force', '--verify', '--verbose',
                '--sign', CODE_SIGN_IDENTITY,
                str(dmg_path)
            ], check=True, capture_output=True)
            logger.info("DMG code signing successful.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"DMG code signing failed: {e.stderr.decode()}")
            return False

    def notarize(self, dmg_path):
        if not (APPLE_ID and APPLE_TEAM_ID and APPLE_APP_SPECIFIC_PASSWORD):
            logger.info("Notarization credentials not provided. Skipping notarization.")
            return False
        logger.info("Submitting DMG for notarization...")
        try:
            # Submit for notarization
            submit = subprocess.run([
                'xcrun', 'altool', '--notarize-app',
                '--primary-bundle-id', f"com.secondbrain.app.{self.version}",
                '--username', APPLE_ID,
                '--password', APPLE_APP_SPECIFIC_PASSWORD,
                '--team-id', APPLE_TEAM_ID,
                '--file', str(dmg_path)
            ], check=True, capture_output=True)
            logger.info(f"Notarization submitted: {submit.stdout.decode()}")
            self.manifest["notarized"] = True
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Notarization failed: {e.stderr.decode()}")
            return False

    def create_zip(self):
        """Create a ZIP archive from the app bundle"""
        logger.info("Creating ZIP archive...")
        zip_path = self.dist_dir / f"{self.app_name}-{self.version}.zip"
        try:
            shutil.make_archive(
                str(zip_path.with_suffix('')),
                'zip',
                root_dir=self.build_dir,
                base_dir=f"{self.app_name}.app"
            )
            logger.info(f"Created ZIP archive at {zip_path}")
            return zip_path
        except Exception as e:
            logger.error(f"Failed to create ZIP archive: {e}")
            raise

    def verify_package(self, package_path):
        """Verify package integrity"""
        logger.info(f"Verifying package: {package_path}")
        if package_path.suffix == '.dmg':
            try:
                subprocess.run([
                    'hdiutil', 'verify',
                    str(package_path)
                ], check=True, capture_output=True)
                logger.info("DMG verification successful")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"DMG verification failed: {e.stderr.decode()}")
                return False
        elif package_path.suffix == '.zip':
            try:
                subprocess.run([
                    'unzip', '-t',
                    str(package_path)
                ], check=True, capture_output=True)
                logger.info("ZIP verification successful")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"ZIP verification failed: {e.stderr.decode()}")
                return False
        return False

    def test_app(self):
        logger.info("Testing packaged app...")
        try:
            # Try to launch the app in headless mode (simulate)
            result = subprocess.run([
                'open', '-W', str(self.app_bundle)
            ], timeout=10)
            if result.returncode == 0:
                self.manifest["tested"] = True
                logger.info("App launch test successful.")
                return True
            else:
                logger.error("App launch test failed.")
                return False
        except Exception as e:
            logger.error(f"App test failed: {e}")
            return False

    def gui_test(self):
        logger.info("Running GUI test (AppleScript)...")
        try:
            script = f'''tell application "{self.app_name}"
activate
delay 2
quit
end tell'''
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.applescript') as f:
                f.write(script)
                script_path = f.name
            result = subprocess.run(['osascript', script_path], timeout=10)
            os.unlink(script_path)
            if result.returncode == 0:
                logger.info("GUI test successful.")
                self.manifest["gui_tested"] = True
                return True
            else:
                logger.error("GUI test failed.")
                self.manifest["gui_tested"] = False
                return False
        except Exception as e:
            logger.error(f"GUI test error: {e}")
            self.manifest["gui_tested"] = False
            return False

    def integration_test(self):
        logger.info("Running integration test (placeholder)...")
        # Placeholder for future integration tests
        self.manifest["integration_tested"] = False
        return True

    def advanced_integration_test(self):
        logger.info("Running advanced integration test...")
        test_script = Path('tests/integration_test.py')
        if test_script.exists():
            try:
                result = subprocess.run(['python3', str(test_script)], capture_output=True, timeout=60)
                self.manifest["advanced_integration_test"] = {
                    "returncode": result.returncode,
                    "stdout": result.stdout.decode(errors='ignore'),
                    "stderr": result.stderr.decode(errors='ignore')
                }
                if result.returncode == 0:
                    logger.info("Advanced integration test passed.")
                    return True
                else:
                    logger.error("Advanced integration test failed.")
                    return False
            except Exception as e:
                logger.error(f"Advanced integration test error: {e}")
                self.manifest["advanced_integration_test"] = {"error": str(e)}
                return False
        else:
            logger.info("No advanced integration test script found.")
            self.manifest["advanced_integration_test"] = None
            return True

    def add_dashboard_auth(self):
        if not (DASHBOARD_USER and DASHBOARD_PASS):
            return
        logger.info("Adding HTTP basic auth to dashboard...")
        import crypt
        htpasswd_path = self.dist_dir / '.htpasswd'
        htaccess_path = self.dist_dir / '.htaccess'
        # Create .htpasswd
        hashed = crypt.crypt(DASHBOARD_PASS, crypt.mksalt(crypt.METHOD_SHA512))
        with open(htpasswd_path, 'w') as f:
            f.write(f"{DASHBOARD_USER}:{hashed}\n")
        # Create .htaccess
        with open(htaccess_path, 'w') as f:
            f.write(f"""AuthType Basic\nAuthName \"Restricted\"\nAuthUserFile {htpasswd_path.resolve()}\nRequire valid-user\n""")
        logger.info("Dashboard authentication files created.")

    def send_email_notification(self, success):
        if not (EMAIL_NOTIFY and SMTP_SERVER and SMTP_USER and SMTP_PASS):
            return
        logger.info(f"Sending build status email to {EMAIL_NOTIFY}...")
        msg = EmailMessage()
        msg['Subject'] = f"Build {'Success' if success else 'Failure'}: {self.app_name} v{self.version}"
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_NOTIFY
        msg.set_content(f"Build {'succeeded' if success else 'failed'} for {self.app_name} v{self.version}.\nSee dashboard for details.")
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            logger.info("Email notification sent.")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def send_webhook_notification(self, success):
        if not WEBHOOK_URL:
            return
        logger.info(f"Sending webhook notification to {WEBHOOK_URL}...")
        payload = {
            "app": self.app_name,
            "version": self.version,
            "status": "success" if success else "failure",
            "timestamp": datetime.now().isoformat(),
            "dashboard_url": f"dashboard.html"
        }
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=10)
            logger.info("Webhook notification sent.")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    def get_changelog_entry(self):
        for fname in ["CHANGELOG.md", "changelog.txt"]:
            path = Path(fname)
            if path.exists():
                with open(path) as f:
                    lines = f.readlines()
                # Find the latest entry (assume markdown or text format)
                entry = []
                for line in lines:
                    if line.strip().startswith('#') or line.strip().lower().startswith('version'):
                        if entry:
                            break
                        entry = [line.strip()]
                    elif entry is not None:
                        entry.append(line.strip())
                return '\n'.join(entry)
        return None

    def generate_dashboard(self):
        logger.info("Generating HTML dashboard...")
        dashboard_path = self.dist_dir / "dashboard.html"
        manifest_path = self.dist_dir / f"{self.app_name}-{self.version}-manifest.json"
        dmg_path = self.dist_dir / f"{self.app_name}-{self.version}.dmg"
        zip_path = self.dist_dir / f"{self.app_name}-{self.version}.zip"
        changelog = self.get_changelog_entry()
        encrypted = ENCRYPT_ARTIFACTS and ENCRYPTION_PASSWORD
        enc_note = ''
        if encrypted:
            enc_note = f"""
            <div style='border:1px solid #c00;padding:1em;margin:1em 0;background:#fee;'>
            <b>Note:</b> Artifacts are encrypted.<br>
            <b>Password:</b> <code>{ENCRYPTION_PASSWORD}</code><br>
            <b>To decrypt:</b><br>
            <pre>openssl aes-256-cbc -d -in &lt;artifact&gt;.enc -out &lt;artifact&gt; -k {ENCRYPTION_PASSWORD}</pre>
            </div>
            """
        html = f"""
        <html><head><title>{self.app_name} Build Dashboard</title>
        <script>
        async function updateDownloads() {{
            let resp = await fetch('/api/downloads');
            if (!resp.ok) return;
            let data = await resp.json();
            for (const [file, count] of Object.entries(data)) {{
                let el = document.getElementById('dl-' + file);
                if (el) el.textContent = count;
            }}
        }}
        window.onload = updateDownloads;
        </script>
        </head><body>
        <h1>{self.app_name} v{self.version} Build Dashboard</h1>
        {enc_note}
        <ul>
            <li><a href='{dmg_path.name}{".enc" if encrypted else ""}'>Download DMG{'.enc' if encrypted else ''}</a> (<span id='dl-{dmg_path.name}{".enc" if encrypted else ""}'>0</span> downloads)</li>
            <li><a href='{zip_path.name}{".enc" if encrypted else ""}'>Download ZIP{'.enc' if encrypted else ''}</a> (<span id='dl-{zip_path.name}{".enc" if encrypted else ""}'>0</span> downloads)</li>
            <li><a href='{manifest_path.name}'>View Manifest</a></li>
        </ul>
        <h2>Build Status</h2>
        <pre>{json.dumps(self.manifest, indent=2)}</pre>
        {f'<h2>Changelog</h2><pre>{changelog}</pre>' if changelog else ''}
        <footer><small>Generated: {datetime.now().isoformat()}</small></footer>
        </body></html>
        """
        with open(dashboard_path, 'w') as f:
            f.write(html)
        logger.info(f"Dashboard generated at {dashboard_path}")
        self.add_dashboard_auth()

    def deploy(self, dmg_path, zip_path):
        if not DEPLOY_TARGET:
            logger.info("No deployment target specified. Skipping deployment.")
            return False
        logger.info(f"Deploying to {DEPLOY_TARGET} ...")
        try:
            if DEPLOY_TARGET.startswith('s3://'):
                subprocess.run(['aws', 's3', 'cp', str(dmg_path), DEPLOY_TARGET], check=True)
                subprocess.run(['aws', 's3', 'cp', str(zip_path), DEPLOY_TARGET], check=True)
            elif DEPLOY_TARGET.startswith('scp:'):
                # Format: scp:user@host:/path
                scp_target = DEPLOY_TARGET[4:]
                subprocess.run(['scp', str(dmg_path), scp_target], check=True)
                subprocess.run(['scp', str(zip_path), scp_target], check=True)
            else:
                logger.warning("Unknown deployment target format.")
                return False
            self.manifest["deployed"] = True
            logger.info("Deployment successful.")
            return True
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    def deploy_ftp(self, dmg_path, zip_path):
        if not FTP_TARGET:
            return False
        logger.info(f"Deploying to FTP: {FTP_TARGET}")
        try:
            for artifact in [dmg_path, zip_path]:
                subprocess.run([
                    'lftp', '-e', f'put {artifact}; bye', FTP_TARGET
                ], check=True)
            self.manifest["deployed_ftp"] = True
            logger.info("FTP deployment successful.")
            return True
        except Exception as e:
            logger.error(f"FTP deployment failed: {e}")
            self.manifest["deployed_ftp"] = False
            return False

    def deploy_gdrive(self, dmg_path, zip_path):
        if not GDRIVE_FOLDER_ID:
            return False
        logger.info(f"Deploying to Google Drive folder: {GDRIVE_FOLDER_ID}")
        try:
            for artifact in [dmg_path, zip_path]:
                subprocess.run([
                    'gdrive', 'upload', '--parent', GDRIVE_FOLDER_ID, str(artifact)
                ], check=True)
            self.manifest["deployed_gdrive"] = True
            logger.info("Google Drive deployment successful.")
            return True
        except Exception as e:
            logger.error(f"Google Drive deployment failed: {e}")
            self.manifest["deployed_gdrive"] = False
            return False

    def save_manifest(self):
        """Save the manifest file"""
        manifest_path = self.dist_dir / f"{self.app_name}-{self.version}-manifest.json"
        # Add manifest hash
        manifest_json = json.dumps(self.manifest, indent=2)
        manifest_hash = hashlib.sha256(manifest_json.encode()).hexdigest()
        self.manifest["manifest_hash"] = manifest_hash
        with open(manifest_path, 'w') as f:
            f.write(manifest_json)
        logger.info(f"Saved manifest to {manifest_path}")

    def send_sms_notification(self, success):
        if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TWILIO_TO):
            return
        logger.info(f"Sending SMS notification to {TWILIO_TO}...")
        body = f"Build {'succeeded' if success else 'failed'} for {self.app_name} v{self.version}."
        try:
            resp = requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json',
                data={
                    'From': TWILIO_FROM,
                    'To': TWILIO_TO,
                    'Body': body
                },
                auth=(TWILIO_SID, TWILIO_TOKEN),
                timeout=10
            )
            if resp.status_code == 201:
                logger.info("SMS notification sent.")
            else:
                logger.error(f"Failed to send SMS: {resp.text}")
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")

    def send_teams_notification(self, success):
        if not TEAMS_WEBHOOK_URL:
            return
        logger.info(f"Sending Teams notification to {TEAMS_WEBHOOK_URL}...")
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": f"Build {'Success' if success else 'Failure'}: {self.app_name}",
            "themeColor": "0076D7" if success else "FF0000",
            "title": f"Build {'Success' if success else 'Failure'}: {self.app_name} v{self.version}",
            "text": f"Build {'succeeded' if success else 'failed'} for {self.app_name} v{self.version}."
        }
        try:
            requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=10)
            logger.info("Teams notification sent.")
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")

    def cleanup_old_artifacts(self):
        logger.info(f"Applying artifact retention policy: keep last {ARTIFACT_RETENTION} builds.")
        builds = sorted(self.dist_dir.glob(f"{self.app_name}-*.dmg"), key=os.path.getmtime, reverse=True)
        for old in builds[ARTIFACT_RETENTION:]:
            try:
                logger.info(f"Removing old artifact: {old}")
                old.unlink()
                # Remove associated zip and manifest
                for ext in ['.zip', '-manifest.json']:
                    related = old.with_suffix(ext) if ext != '-manifest.json' else old.with_name(old.name.replace('.dmg', '-manifest.json'))
                    if related.exists():
                        related.unlink()
            except Exception as e:
                logger.error(f"Failed to remove old artifact {old}: {e}")

    def encrypt_artifact(self, path):
        if not ENCRYPT_ARTIFACTS or not ENCRYPTION_PASSWORD:
            return path
        logger.info(f"Encrypting artifact: {path}")
        encrypted_path = path.with_suffix(path.suffix + '.enc')
        # Use openssl for encryption
        cmd = [
            'openssl', 'aes-256-cbc', '-salt', '-in', str(path), '-out', str(encrypted_path),
            '-k', ENCRYPTION_PASSWORD
        ]
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Encrypted artifact at {encrypted_path}")
            return encrypted_path
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return path

    def mirror_to_cdn(self, artifact_path):
        if not CDN_MIRROR_CMD:
            return
        logger.info(f"Mirroring artifact to CDN: {artifact_path}")
        try:
            # Replace placeholder in command
            cmd = CDN_MIRROR_CMD.replace('{artifact}', str(artifact_path))
            subprocess.run(cmd, shell=True, check=True)
            logger.info("CDN mirroring command executed.")
        except Exception as e:
            logger.error(f"CDN mirroring failed: {e}")

    def package(self):
        """Main packaging process"""
        try:
            # Create backup
            backup_path = self.create_backup()
            
            # Calculate checksums
            self.calculate_checksums()
            
            # Create distribution packages
            dmg_path = self.create_dmg()
            zip_path = self.create_zip()
            
            # Encrypt artifacts if enabled
            dmg_path = self.encrypt_artifact(dmg_path)
            zip_path = self.encrypt_artifact(zip_path)
            
            # Verify packages
            if not all([
                self.verify_package(dmg_path),
                self.verify_package(zip_path)
            ]):
                raise Exception("Package verification failed")
            
            # Save manifest
            self.save_manifest()
            
            # Code sign
            if self.code_sign():
                logger.info("App code signed.")
            
            # Code sign DMG
            self.code_sign_dmg(dmg_path)
            
            # Notarize
            if NOTARIZE:
                self.notarize(dmg_path)
            
            # Test app
            self.test_app()
            
            # GUI test
            self.gui_test()
            
            # Integration test
            self.integration_test()
            
            # Advanced integration test
            self.advanced_integration_test()
            
            # Deploy
            self.deploy(dmg_path, zip_path)
            
            # Deploy to FTP
            self.deploy_ftp(dmg_path, zip_path)
            
            # Deploy to Google Drive
            self.deploy_gdrive(dmg_path, zip_path)
            
            # Generate dashboard
            self.generate_dashboard()
            
            # Cleanup old artifacts
            self.cleanup_old_artifacts()
            
            # Mirror to CDN
            self.mirror_to_cdn(dmg_path)
            self.mirror_to_cdn(zip_path)
            
            logger.info("Packaging completed successfully")
            logger.info(f"Distribution files available in {self.dist_dir}")
            
            self.send_email_notification(True)
            self.send_webhook_notification(True)
            self.send_sms_notification(True)
            self.send_teams_notification(True)
            
            return True
            
        except Exception as e:
            logger.error(f"Packaging failed: {e}")
            if backup_path:
                logger.info(f"Restoring from backup: {backup_path}")
                if self.app_bundle.exists():
                    shutil.rmtree(self.app_bundle)
                shutil.copytree(backup_path, self.app_bundle)
            self.send_email_notification(False)
            self.send_webhook_notification(False)
            self.send_sms_notification(False)
            self.send_teams_notification(False)
            return False

def main():
    packager = AppPackager()
    success = packager.package()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 