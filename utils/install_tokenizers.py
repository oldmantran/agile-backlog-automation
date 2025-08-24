"""
Optional tokenizer installation script.
These tokenizers provide more accurate token counting but are not required.
The system will fall back to character-based approximation if not installed.
"""

import subprocess
import sys

def install_tokenizers():
    """Install optional tokenizer packages for better token counting."""
    
    packages = [
        ("tiktoken", "0.7.0"),  # OpenAI's tokenizer
        # Note: Anthropic and other providers don't have public tokenizers
    ]
    
    print("Installing optional tokenizer packages...")
    print("These provide more accurate token counting but are not required.\n")
    
    for package, version in packages:
        try:
            print(f"Installing {package}=={version}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", f"{package}=={version}"
            ])
            print(f"✓ {package} installed successfully\n")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}, will use approximation\n")
        except Exception as e:
            print(f"✗ Error installing {package}: {e}\n")
    
    print("\nTokenizer installation complete.")
    print("The system will use these for accurate token counting when available.")
    print("If not installed, character-based approximation will be used.")

if __name__ == "__main__":
    install_tokenizers()