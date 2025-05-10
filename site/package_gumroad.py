"""
Package Gumroad assets for AI Business Starter Pack deployment
"""
import os
import json
import shutil
import logging
import zipfile
import hashlib
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GumroadPackager:
    def __init__(self, base_dir="site/gumroad"):
        """Initialize the Gumroad packager."""
        self.base_dir = base_dir
        self.assets_dir = os.path.join(base_dir, "assets")
        self.package_dir = os.path.join(base_dir, "package")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.package_dir, exist_ok=True)
        
    def validate_assets(self) -> bool:
        """Validate required assets exist."""
        required_files = [
            os.path.join(self.assets_dir, "cover_mockup.jpg"),
            os.path.join(self.assets_dir, "ai_starter_pack", "product_intro.mp3"),
            os.path.join(self.assets_dir, "ai_starter_pack", "NjanjaStorefront_Package.zip"),
            os.path.join(self.base_dir, "ai_starter_pack_product.json")
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            logger.error("Missing required files:")
            for file in missing_files:
                logger.error(f"  - {file}")
            return False
            
        return True
        
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()
        
    def create_manifest(self) -> dict:
        """Create package manifest with file information."""
        manifest = {
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "files": {}
        }
        
        for root, _, files in os.walk(self.assets_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.assets_dir)
                
                manifest["files"][relative_path] = {
                    "size": os.path.getsize(file_path),
                    "checksum": self.calculate_checksum(file_path),
                    "modified": datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).isoformat()
                }
                
        return manifest
        
    def package_assets(self, output_path: str = None) -> str:
        """Package Gumroad assets into a zip file."""
        try:
            # Validate assets
            if not self.validate_assets():
                raise ValueError("Missing required assets")
                
            # Set output path
            if not output_path:
                output_path = os.path.join(
                    self.package_dir,
                    f"Njanja_Gumroad_AIStarterPack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                )
                
            # Create manifest
            manifest = self.create_manifest()
            manifest_path = os.path.join(self.package_dir, "manifest.json")
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
                
            # Create zip file
            logger.info(f"Creating package: {output_path}")
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add assets
                for root, _, files in os.walk(self.assets_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.base_dir)
                        zipf.write(file_path, arcname)
                        
                # Add product configuration
                product_config = os.path.join(self.base_dir, "ai_starter_pack_product.json")
                if os.path.exists(product_config):
                    zipf.write(product_config, "ai_starter_pack_product.json")
                    
                # Add manifest
                zipf.write(manifest_path, "manifest.json")
                
            # Remove temporary manifest file
            os.remove(manifest_path)
            
            # Calculate package checksum
            package_checksum = self.calculate_checksum(output_path)
            logger.info(f"Package checksum: {package_checksum}")
            
            # Create checksum file
            checksum_path = f"{output_path}.sha256"
            with open(checksum_path, 'w') as f:
                f.write(f"{package_checksum}  {os.path.basename(output_path)}")
                
            logger.info(f"Package created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to package assets: {e}")
            raise
            
    def verify_package(self, package_path: str) -> bool:
        """Verify package integrity."""
        try:
            # Check if package exists
            if not os.path.exists(package_path):
                logger.error(f"Package not found: {package_path}")
                return False
                
            # Verify checksum
            checksum_path = f"{package_path}.sha256"
            if os.path.exists(checksum_path):
                with open(checksum_path, 'r') as f:
                    expected_checksum = f.read().split()[0]
                    
                actual_checksum = self.calculate_checksum(package_path)
                
                if actual_checksum != expected_checksum:
                    logger.error("Package checksum verification failed")
                    return False
                    
            # Verify zip file
            with zipfile.ZipFile(package_path, 'r') as zipf:
                if zipf.testzip() is not None:
                    logger.error("Package integrity check failed")
                    return False
                    
            logger.info("Package verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify package: {e}")
            return False

def main():
    """Package Gumroad assets for deployment."""
    try:
        # Initialize packager
        packager = GumroadPackager()
        
        # Package assets
        package_path = packager.package_assets()
        
        # Verify package
        if packager.verify_package(package_path):
            print(f"\nPackage created successfully: {package_path}")
            print("\nNext steps:")
            print("1. Review the package contents")
            print("2. Upload to Gumroad")
            print("3. Verify the upload")
        else:
            print("\nPackage verification failed. Please check the logs.")
        
    except Exception as e:
        logger.error(f"Failed to package assets: {e}")
        raise

if __name__ == '__main__':
    main() 