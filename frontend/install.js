const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  red: '\x1b[31m'
};

console.log(`${colors.blue}==========================================${colors.reset}`);
console.log(`${colors.blue}   Agile Backlog Automation Frontend Setup${colors.reset}`);
console.log(`${colors.blue}==========================================${colors.reset}\n`);

// Function to execute shell commands
function executeCommand(command) {
  try {
    execSync(command, { stdio: 'inherit' });
    return true;
  } catch (error) {
    console.error(`${colors.red}Command failed: ${command}${colors.reset}`);
    console.error(error.message);
    return false;
  }
}

// Check if Node.js and npm are installed
console.log(`${colors.cyan}Checking prerequisites...${colors.reset}`);

try {
  const nodeVersion = execSync('node --version').toString().trim();
  console.log(`${colors.green}✓ Node.js ${nodeVersion} is installed${colors.reset}`);
  
  const npmVersion = execSync('npm --version').toString().trim();
  console.log(`${colors.green}✓ npm ${npmVersion} is installed${colors.reset}`);
} catch (error) {
  console.error(`${colors.red}Error: Node.js and npm are required to continue.${colors.reset}`);
  console.error(`Please install Node.js from https://nodejs.org/`);
  process.exit(1);
}

console.log(`\n${colors.cyan}Installing dependencies...${colors.reset}`);
console.log(`This may take a few minutes.\n`);

// Install dependencies
if (!executeCommand('cd frontend && npm install')) {
  console.error(`${colors.red}Failed to install dependencies.${colors.reset}`);
  process.exit(1);
}

// Create .env file
console.log(`\n${colors.cyan}Creating environment configuration...${colors.reset}`);
const envContent = `REACT_APP_API_URL=http://localhost:8000/api`;

fs.writeFileSync(path.join(__dirname, 'frontend', '.env'), envContent);
console.log(`${colors.green}✓ Created .env file${colors.reset}`);

console.log(`\n${colors.green}==========================================${colors.reset}`);
console.log(`${colors.green}✓ Frontend setup complete!${colors.reset}`);
console.log(`${colors.green}==========================================${colors.reset}\n`);

console.log(`${colors.yellow}To start the development server:${colors.reset}`);
console.log(`${colors.cyan}cd frontend${colors.reset}`);
console.log(`${colors.cyan}npm start${colors.reset}\n`);

console.log(`This will launch the application on http://localhost:3000\n`);

process.exit(0);
