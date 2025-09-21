# MShell Email Client

A modern, secure email client for Linux with a clean interface and essential features.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)

## Features

- 📧 Multiple email account support
- 🔒 Secure password storage
- 📎 File attachments support
- 🔄 Auto-refresh functionality
- 📱 Modern, responsive UI
- 🚀 Quick setup for Gmail and Outlook
- 💻 Desktop integration

## Quick Start

### Prerequisites

```bash
# Install Python 3.8+ if not already installed
sudo apt install python3 python3-pip python3-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Run the application
python src/mshell.py

# Install desktop entry (optional)
python src/mshell.py --install
```

## Email Account Setup

1. Click "Account" → "Add Account"
2. Enter your email address
3. For Gmail:
   - Enable 2FA in your Google Account
   - Generate an App Password
   - Use the App Password instead of your regular password
4. For Outlook:
   - Use your regular email and password
5. For other providers:
   - Enter SMTP/IMAP settings manually

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/mshell.git
cd mshell

# Install dev dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## Project Structure

```
mshell/
├── src/
│   └── mshell.py      # Main application
├── requirements.txt    # Dependencies
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GPL 3.0 License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the GUI framework
- Python keyring for secure password storage
