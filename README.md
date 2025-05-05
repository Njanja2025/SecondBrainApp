# SecondBrain AI Agent

An advanced AI-powered system with blockchain integration, voice control, and security features.

## Features

- **Voice Control**: Natural voice commands for system interaction
- **Blockchain Integration**: Create and deploy smart contracts
- **Security Agent**: Smart contract vulnerability scanning
- **Web3 Wallet**: Ethereum wallet management
- **NjanjaCoin**: Custom ERC20 token with staking and governance
- **Phantom Core**: Advanced system security and monitoring

## System Requirements

- macOS 10.12 or higher
- Python 3.8 or higher
- 2+ CPU cores
- 4GB+ available memory
- 1GB+ free disk space

## Prerequisites

- Python 3.8+
- ffmpeg (for voice processing)
- Node.js and npm (for smart contract compilation)
- AWS CLI configured with appropriate credentials
- GitHub account with repository access

## Environment Setup

1. Create a `.env` file with required credentials:
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Blockchain
INFURA_API_KEY=your_infura_key
PRIVATE_KEY=your_wallet_private_key
ETHEREUM_NETWORK=sepolia

# GitHub
GITHUB_TOKEN=your_github_token
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/secondbrain.git
cd secondbrain
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

## Building the App

1. Build the macOS app bundle:
```bash
./deploy.sh
```

2. For deployment to all channels:
```bash
./deploy.sh --upload
```

This will:
- Build the .app bundle
- Create distribution package
- Upload to AWS S3
- Create GitHub release
- Update njanja.net/phantom

## Security Features

### Phantom Core
- Encrypted operation logging
- Real-time system monitoring
- Threat detection
- Resource usage tracking
- Secure startup verification

### Blockchain Security
- Smart contract vulnerability scanning
- Transaction monitoring
- Secure wallet management
- Automated auditing

## Deployment Channels

The app is automatically deployed to:
1. GitHub Releases
2. AWS S3 bucket (njanja-phantom)
3. njanja.net/phantom

## Monitoring

The system includes:
- Resource usage monitoring
- Security threat detection
- Performance metrics
- Error tracking
- Audit logging

## Development

1. Fork the repository
2. Create your feature branch:
```bash
git checkout -b feature/amazing-feature
```
3. Commit your changes:
```bash
git commit -m 'Add amazing feature'
```
4. Push to the branch:
```bash
git push origin feature/amazing-feature
```
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

Report security vulnerabilities to security@njanja.net

## Support

For support, email support@njanja.net or join our Discord server. 