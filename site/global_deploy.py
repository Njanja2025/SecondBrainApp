"""
Global deployment system for the AI Business Starter Pack
"""
import os
import sys
import json
import shutil
import logging
import zipfile
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GlobalDeployer:
    def __init__(self):
        """Initialize the global deployer."""
        self.base_path = Path("/mnt/data/global_storefront")
        self.config = self.load_config()
        self.version_file = self.base_path / "version.json"
        self.backup_dir = self.base_path / "backups"
        self.checksums_file = self.base_path / "checksums.json"
        
    def load_config(self) -> Dict:
        """Load deployment configuration."""
        config_path = Path("site/deploy_config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            's3_bucket': 'njanja-global',
            'cloudfront_distribution': 'your-distribution-id',
            'regions': {
                'africa': {
                    'payment': 'paystack',
                    'currency': 'ZAR',
                    'price': 499.00
                },
                'global': {
                    'payment': 'stripe',
                    'currency': 'USD',
                    'price': 29.99
                }
            },
            'backup_retention_days': 30,
            'monitoring': {
                'endpoints': [
                    'https://njanja.net',
                    'https://global.njanja.net'
                ],
                'check_interval': 300  # 5 minutes
            }
        }
        
    def create_directory_structure(self) -> bool:
        """Create the global directory structure."""
        try:
            paths = [
                "gumroad/ai_starter_pack_gumroad.txt",
                "stripe/stripe_checkout.html",
                "redirect/index.html",
                "voice_scripts/global_intro.txt",
                "backups",
                "logs",
                "monitoring"
            ]
            
            for path in paths:
                full_path = self.base_path / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directory structure: {e}")
            return False
            
    def create_content_files(self) -> bool:
        """Create content files with region-specific content."""
        try:
            # Gumroad link
            with open(self.base_path / "gumroad/ai_starter_pack_gumroad.txt", "w") as f:
                f.write("https://gumroad.com/l/njanja_ai_starter_pack")
                
            # Stripe checkout
            stripe_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Stripe Checkout - AI Business Starter Pack</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://js.stripe.com/v3/"></script>
                <style>
                    body { font-family: 'Inter', sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .price { font-size: 2em; color: #4F46E5; }
                    .button { 
                        background: #10B981;
                        color: white;
                        padding: 1rem 2rem;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AI Business Starter Pack</h1>
                    <p class="price">$29.99 USD</p>
                    <button class="button" onclick="checkout()">Buy Now</button>
                </div>
                <script>
                    const stripe = Stripe('pk_test_your_key');
                    function checkout() {
                        stripe.redirectToCheckout({
                            lineItems: [{
                                price: 'price_H5ggYwtDq4fbrJ',
                                quantity: 1
                            }],
                            mode: 'payment',
                            successUrl: 'https://njanja.net/success',
                            cancelUrl: 'https://njanja.net/cancel'
                        });
                    }
                </script>
            </body>
            </html>
            """
            with open(self.base_path / "stripe/stripe_checkout.html", "w") as f:
                f.write(stripe_html)
                
            # Redirect page
            redirect_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Njanja Global Redirect</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script>
                    function getRegion() {
                        const country = navigator.language || navigator.userLanguage;
                        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                        
                        // Check for African countries
                        const africanCountries = ['ZA', 'NG', 'KE', 'GH', 'EG'];
                        if (africanCountries.some(code => country.includes(code))) {
                            return 'africa';
                        }
                        
                        // Check for African timezones
                        const africanTimezones = ['Africa/'];
                        if (africanTimezones.some(tz => timezone.includes(tz))) {
                            return 'africa';
                        }
                        
                        return 'global';
                    }
                    
                    window.onload = function() {
                        const region = getRegion();
                        if (region === 'africa') {
                            window.location.href = '../paystack_test_checkout.html';
                        } else {
                            window.location.href = '../stripe/stripe_checkout.html';
                        }
                    }
                </script>
            </head>
            <body>
                <p>Redirecting based on your location...</p>
            </body>
            </html>
            """
            with open(self.base_path / "redirect/index.html", "w") as f:
                f.write(redirect_html)
                
            # Global intro script
            intro_text = """
            Welcome to Njanja Global. Whether you're in Africa, America, or Asia — 
            we've got powerful AI tools ready for you. Let's build your digital future.
            
            Our AI Business Starter Pack includes:
            - AI automation tools to streamline your workflow
            - Customizable eBook with comprehensive guides
            - Ready-to-use marketing templates
            - 24/7 support and updates
            
            Choose your preferred payment method and start your journey today.
            """
            with open(self.base_path / "voice_scripts/global_intro.txt", "w") as f:
                f.write(intro_text)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to create content files: {e}")
            return False
            
    def generate_voice_over(self) -> bool:
        """Generate voice-over for global intro."""
        try:
            script_path = self.base_path / "voice_scripts/global_intro.txt"
            output_path = self.base_path / "voice_scripts/global_intro.mp3"
            
            # Use macOS say command
            if sys.platform == 'darwin':
                subprocess.run([
                    'say', '-v', 'Samantha',
                    '-o', str(output_path),
                    '-f', str(script_path)
                ], check=True)
                
                # Convert to MP3 if ffmpeg is available
                if shutil.which('ffmpeg'):
                    temp_aiff = output_path
                    output_path = output_path.with_suffix('.mp3')
                    subprocess.run([
                        'ffmpeg', '-y', '-i', str(temp_aiff),
                        '-codec:a', 'libmp3lame', '-qscale:a', '2',
                        str(output_path)
                    ], check=True)
                    temp_aiff.unlink()
                    
                return True
            else:
                logger.error("Voice generation requires macOS")
                return False
                
        except Exception as e:
            logger.error(f"Failed to generate voice-over: {e}")
            return False
            
    def create_backup(self) -> bool:
        """Create a backup of the current deployment."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all files except backups and logs
            for item in self.base_path.glob("*"):
                if item.name not in ['backups', 'logs']:
                    if item.is_file():
                        shutil.copy2(item, backup_path / item.name)
                    else:
                        shutil.copytree(item, backup_path / item.name)
                        
            # Create backup archive
            backup_zip = self.backup_dir / f"backup_{timestamp}.zip"
            with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in backup_path.rglob("*"):
                    if item.is_file():
                        zipf.write(item, item.relative_to(backup_path))
                        
            # Clean up temporary directory
            shutil.rmtree(backup_path)
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
            
    def cleanup_old_backups(self):
        """Remove backups older than retention period."""
        try:
            retention_days = self.config['backup_retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for backup_file in self.backup_dir.glob("backup_*.zip"):
                try:
                    timestamp = datetime.strptime(
                        backup_file.stem.split('_')[1],
                        "%Y%m%d_%H%M%S"
                    )
                    if timestamp < cutoff_date:
                        backup_file.unlink()
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            
    def calculate_checksums(self) -> Dict[str, str]:
        """Calculate checksums for all files."""
        checksums = {}
        try:
            for file_path in self.base_path.rglob("*"):
                if file_path.is_file():
                    sha256_hash = hashlib.sha256()
                    with open(file_path, "rb") as f:
                        for byte_block in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(byte_block)
                    checksums[str(file_path.relative_to(self.base_path))] = \
                        sha256_hash.hexdigest()
                        
            with open(self.checksums_file, 'w') as f:
                json.dump(checksums, f, indent=2)
                
            return checksums
            
        except Exception as e:
            logger.error(f"Failed to calculate checksums: {e}")
            return {}
            
    def deploy_to_s3(self) -> bool:
        """Deploy files to S3 and invalidate CloudFront cache."""
        try:
            s3 = boto3.client('s3')
            cloudfront = boto3.client('cloudfront')
            
            # Upload files to S3
            for file_path in self.base_path.rglob("*"):
                if file_path.is_file():
                    key = str(file_path.relative_to(self.base_path))
                    s3.upload_file(
                        str(file_path),
                        self.config['s3_bucket'],
                        key,
                        ExtraArgs={'ContentType': self.get_content_type(file_path)}
                    )
                    
            # Invalidate CloudFront cache
            cloudfront.create_invalidation(
                DistributionId=self.config['cloudfront_distribution'],
                InvalidationBatch={
                    'Paths': {
                        'Quantity': 1,
                        'Items': ['/*']
                    },
                    'CallerReference': str(datetime.now().timestamp())
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy to S3: {e}")
            return False
            
    def get_content_type(self, file_path: Path) -> str:
        """Get the content type for a file."""
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.mp3': 'audio/mpeg',
            '.txt': 'text/plain',
            '.zip': 'application/zip'
        }
        return content_types.get(file_path.suffix, 'application/octet-stream')
        
    def monitor_endpoints(self) -> List[Dict]:
        """Monitor deployment endpoints."""
        issues = []
        for endpoint in self.config['monitoring']['endpoints']:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code != 200:
                    issues.append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'error': 'Non-200 response'
                    })
            except requests.exceptions.RequestException as e:
                issues.append({
                    'endpoint': endpoint,
                    'status': None,
                    'error': str(e)
                })
        return issues
        
    def create_package(self) -> bool:
        """Create the global deployment package."""
        try:
            # Create backup
            if not self.create_backup():
                return False
                
            # Create directory structure
            if not self.create_directory_structure():
                return False
                
            # Create content files
            if not self.create_content_files():
                return False
                
            # Generate voice-over
            if not self.generate_voice_over():
                return False
                
            # Calculate checksums
            checksums = self.calculate_checksums()
            if not checksums:
                return False
                
            # Create package
            package_path = Path("/mnt/data/Njanja_GlobalStorefront_Package.zip")
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.base_path.rglob("*"):
                    if file_path.is_file():
                        zipf.write(
                            file_path,
                            file_path.relative_to(self.base_path)
                        )
                        
            # Deploy to S3
            if not self.deploy_to_s3():
                return False
                
            # Monitor endpoints
            issues = self.monitor_endpoints()
            if issues:
                logger.warning("Deployment monitoring issues:")
                for issue in issues:
                    logger.warning(f"- {issue['endpoint']}: {issue['error']}")
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to create package: {e}")
            return False

def main():
    """Main function to run global deployment."""
    deployer = GlobalDeployer()
    
    if deployer.create_package():
        print("\nGlobal deployment completed successfully!")
        print("\nNext steps:")
        print("1. Verify the package at /mnt/data/Njanja_GlobalStorefront_Package.zip")
        print("2. Check the S3 bucket for uploaded files")
        print("3. Monitor the CloudFront distribution")
        print("4. Test the regional redirects")
    else:
        print("\nGlobal deployment failed. Check the logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main() 