#!/usr/bin/env python3
"""
Modern Email Client - Single File Edition
Installation:
    pip install PyQt6 keyring python-dotenv
Build:
    pyinstaller --onefile --windowed client.py
"""

import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
import keyring
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import json
from datetime import datetime
import subprocess

# Application metadata
APP_NAME = "Modern Email"
APP_VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".config" / "modern-mail"
CONFIG_FILE = CONFIG_DIR / "config.json"
DESKTOP_ENTRY = """
[Desktop Entry]
Version=1.0
Name=Modern Email
Comment=Modern Email Client
Exec={executable_path}
Icon=mail-client
Terminal=false
Type=Application
Categories=Network;Email;
"""

class ModernEmailClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(QSize(1200, 800))
        
        # Initialize configurations
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.load_config()
        
        # Setup UI
        self.setup_ui()
        self.setup_styles()
        
        # Auto refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_emails)
        self.refresh_timer.start(300000)  # 5 minutes

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f2f5; }
            QPushButton { 
                background-color: #0d6efd; 
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0b5ed7; }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 5px;
            }
            QLineEdit, QTextEdit {
                padding: 10px;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
            }
            QLabel { color: #212529; }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk { background-color: #0d6efd; }
        """)

    def setup_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Menu bar
        self.setup_menu()
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"📧 {APP_NAME}")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.addWidget(title)
        
        # Account selector
        self.account_selector = QComboBox()
        self.account_selector.currentTextChanged.connect(self.switch_account)
        header.addWidget(self.account_selector)
        
        layout.addLayout(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        for text, icon, callback in [
            ("New Email", "✉️", self.compose_email),
            ("Refresh", "🔄", self.refresh_emails),
            ("Delete", "🗑️", self.delete_email),
            ("Settings", "⚙️", self.show_settings),
            ("Help", "❓", self.show_help)
        ]:
            btn = QPushButton(f"{icon} {text}")
            btn.clicked.connect(callback)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Email list
        self.email_table = QTableWidget()
        self.email_table.setColumnCount(4)
        self.email_table.setHorizontalHeaderLabels(["Status", "Date", "From", "Subject"])
        self.email_table.horizontalHeader().setStretchLastSection(True)
        self.email_table.setAlternatingRowColors(True)
        self.email_table.doubleClicked.connect(self.view_email)
        layout.addWidget(self.email_table)

    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("New Email", self.compose_email)
        file_menu.addAction("Settings", self.show_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Account menu
        account_menu = menubar.addMenu("&Account")
        account_menu.addAction("Add Account", self.add_account)
        account_menu.addAction("Remove Account", self.remove_account)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("Help", self.show_help)
        help_menu.addAction("About", self.show_about)

    def load_config(self):
        self.config = {}
        if CONFIG_FILE.exists():
            self.config = json.loads(CONFIG_FILE.read_text())
            self.update_account_list()

    def save_config(self):
        CONFIG_FILE.write_text(json.dumps(self.config, indent=2))
        self.update_account_list()

    def update_account_list(self):
        self.account_selector.clear()
        if self.config.get('accounts'):
            self.account_selector.addItems(self.config['accounts'].keys())

    def add_account(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Email Account")
        layout = QVBoxLayout(dialog)
        
        # Form fields
        form = QFormLayout()
        email = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Email:", email)
        form.addRow("Password:", password)
        layout.addLayout(form)
        
        # Quick setup buttons
        btn_layout = QHBoxLayout()
        providers = {
            "Gmail": ("smtp.gmail.com", 587, "imap.gmail.com", 993),
            "Outlook": ("smtp-mail.outlook.com", 587, "outlook.office365.com", 993)
        }
        
        for provider, settings in providers.items():
            btn = QPushButton(provider)
            btn.clicked.connect(lambda checked, s=settings: self.quick_setup(email, *s))
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        
        # Save button
        save_btn = QPushButton("Save Account")
        save_btn.clicked.connect(lambda: self.save_account(dialog, email.text(), password.text()))
        layout.addWidget(save_btn)
        
        dialog.exec()

    def quick_setup(self, email_field, smtp_server, smtp_port, imap_server, imap_port):
        if not 'accounts' in self.config:
            self.config['accounts'] = {}
            
        self.current_setup = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'imap_server': imap_server,
            'imap_port': imap_port
        }

    def save_account(self, dialog, email, password):
        if hasattr(self, 'current_setup'):
            self.config['accounts'][email] = self.current_setup
            keyring.set_password("modern-mail", email, password)
            self.save_config()
            dialog.accept()
            self.refresh_emails()

    def compose_email(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Compose Email")
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout(dialog)
        
        # Email form
        form = QFormLayout()
        to = QLineEdit()
        subject = QLineEdit()
        form.addRow("To:", to)
        form.addRow("Subject:", subject)
        layout.addLayout(form)
        
        # Rich text editor
        body = QTextEdit()
        layout.addWidget(body)
        
        # Attachment button
        attach_btn = QPushButton("📎 Add Attachment")
        self.attachments = []
        attach_btn.clicked.connect(lambda: self.add_attachment(dialog))
        layout.addWidget(attach_btn)
        
        # Buttons
        buttons = QHBoxLayout()
        send = QPushButton("Send")
        send.clicked.connect(lambda: self.send_email(dialog, to.text(), subject.text(), body.toPlainText()))
        buttons.addWidget(send)
        layout.addLayout(buttons)
        
        dialog.exec()

    def add_attachment(self, parent):
        files, _ = QFileDialog.getOpenFileNames(parent, "Select Attachments")
        self.attachments.extend(files)
        if self.attachments:
            QMessageBox.information(parent, "Attachments", f"Added {len(files)} attachment(s)")

    def send_email(self, dialog, to, subject, body):
        try:
            account = self.account_selector.currentText()
            settings = self.config['accounts'][account]
            password = keyring.get_password("modern-mail", account)
            
            msg = MIMEMultipart()
            msg['From'] = account
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body))
            
            # Add attachments
            for file_path in self.attachments:
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{Path(file_path).name}"')
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(settings['smtp_server'], settings['smtp_port']) as server:
                server.starttls()
                server.login(account, password)
                server.send_message(msg)
            
            QMessageBox.information(dialog, "Success", "Email sent successfully!")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to send email: {str(e)}")

    def refresh_emails(self):
        account = self.account_selector.currentText()
        if not account:
            return
            
        try:
            settings = self.config['accounts'][account]
            password = keyring.get_password("modern-mail", account)
            
            self.progress.setVisible(True)
            with imaplib.IMAP4_SSL(settings['imap_server'], settings['imap_port']) as imap:
                imap.login(account, password)
                imap.select("INBOX")
                
                _, messages = imap.search(None, "ALL")
                emails = []
                
                for num in messages[0].split()[-20:]:
                    _, msg = imap.fetch(num, "(RFC822)")
                    email_msg = email.message_from_bytes(msg[0][1])
                    
                    _, flags = imap.fetch(num, "(FLAGS)")
                    is_read = "\\Seen" in flags[0].decode()
                    
                    emails.append({
                        'id': num,
                        'status': "📨" if is_read else "📩",
                        'date': email.utils.format_datetime(email.utils.parsedate_to_datetime(email_msg['date'])),
                        'from': email_msg['from'],
                        'subject': email_msg['subject'] or "(No Subject)"
                    })
                
                self.email_table.setRowCount(len(emails))
                for i, data in enumerate(reversed(emails)):
                    for j, key in enumerate(['status', 'date', 'from', 'subject']):
                        self.email_table.setItem(i, j, QTableWidgetItem(str(data[key])))
                        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch emails: {str(e)}")
        finally:
            self.progress.setVisible(False)

    def view_email(self, index):
        account = self.account_selector.currentText()
        if not account:
            return
            
        try:
            settings = self.config['accounts'][account]
            password = keyring.get_password("modern-mail", account)
            
            row = index.row()
            with imaplib.IMAP4_SSL(settings['imap_server'], settings['imap_port']) as imap:
                imap.login(account, password)
                imap.select("INBOX")
                
                _, messages = imap.search(None, "ALL")
                email_id = messages[0].split()[-20:][row]
                
                _, msg = imap.fetch(email_id, "(RFC822)")
                email_msg = email.message_from_bytes(msg[0][1])
                
                body = ""
                if email_msg.is_multipart():
                    for part in email_msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_msg.get_payload(decode=True).decode()
                
                # Show email viewer
                viewer = QDialog(self)
                viewer.setWindowTitle("View Email")
                viewer.setMinimumSize(800, 600)
                layout = QVBoxLayout(viewer)
                
                # Header info
                header = QFrame()
                header.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
                header_layout = QVBoxLayout(header)
                
                for key in ['from', 'to', 'subject', 'date']:
                    if email_msg[key]:
                        label = QLabel(f"<b>{key.title()}:</b> {email_msg[key]}")
                        header_layout.addWidget(label)
                
                layout.addWidget(header)
                
                # Body
                body_text = QTextEdit()
                body_text.setReadOnly(True)
                body_text.setPlainText(body)
                layout.addWidget(body_text)
                
                # Attachments
                if email_msg.is_multipart():
                    attachments = []
                    for part in email_msg.walk():
                        if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition'):
                            attachments.append(part.get_filename())
                    
                    if attachments:
                        attach_label = QLabel("📎 Attachments: " + ", ".join(attachments))
                        layout.addWidget(attach_label)
                
                viewer.exec()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open email: {str(e)}")

    def create_desktop_entry(self):
        try:
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / "modern-email.desktop"
            desktop_file.write_text(
                DESKTOP_ENTRY.format(executable_path=sys.argv[0])
            )
            desktop_file.chmod(0o755)
            
            QMessageBox.information(self, "Success", 
                "Desktop entry created successfully!\nThe application will appear in your system menu.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create desktop entry: {str(e)}")

    def show_about(self):
        QMessageBox.about(self, "About Modern Email",
            f"""<h1>Modern Email Client</h1>
            <p>Version: {APP_VERSION}</p>
            <p>A modern, secure email client for Linux.</p>
            <p>Features:</p>
            <ul>
                <li>Multiple account support</li>
                <li>Secure password storage</li>
                <li>File attachments</li>
                <li>Auto-refresh</li>
            </ul>""")

def main():
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Create and show window
    window = ModernEmailClient()
    window.show()
    
    # Create desktop entry if running as installed application
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        window.create_desktop_entry()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
