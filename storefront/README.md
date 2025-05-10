# Njanja Storefront Package

## Overview
This package contains everything you need to set up your digital storefront, including:
- AI Business Starter Pack product files
- Voice-over scripts and audio
- Paystack test checkout integration

## Directory Structure
```
storefront/
├── docs/                    # Documentation
├── products/               # Product files
│   └── ai_business_starter_pack/
│       ├── assets/        # Product assets
│       ├── description.md # Product description
│       └── price.txt     # Product pricing
├── voice_scripts/         # Voice-over scripts
└── paystack_test_checkout.html
```

## Setup Instructions

### 1. Voice-over Generation
The package includes a script to generate voice-overs using macOS's built-in `say` command:
```bash
python generate_voiceover.py
```

### 2. Product Setup
1. Review and customize the product description in `products/ai_business_starter_pack/description.md`
2. Update pricing in `products/ai_business_starter_pack/price.txt`
3. Customize the cover mockup in `products/ai_business_starter_pack/assets/cover_mockup.jpg`

### 3. Payment Integration
1. Update the Paystack test key in `paystack_test_checkout.html`
2. Test the checkout process using the test mode
3. Replace with production key when ready

## Requirements
- macOS for voice-over generation
- ffmpeg (optional) for MP3 conversion
- Python 3.6+

## Support
For support, contact support@njanja.net
