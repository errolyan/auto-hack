#!/usr/bin/env python3
"""
autohack with MCP Integration for Kali Linux
Usage: python claude_chat.py [--mcp] [--mcp-server URL] [--model MODEL]
By: Christopher M. Burkett DBA: CyberAndFires
GitHub: https://github.com/ChrisBurkett/claudestrike
"""

import anthropic
import os
import sys
import argparse
import requests
import json
import readline
from typing import Optional, Dict, Any, List

# Try to import OpenAI and Google Gemini libraries
try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Colors for terminal output
class Colors:
    # Regular colors
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Background colors
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_RED = '\033[41m'
    BG_PURPLE = '\033[45m'
    BG_CYAN = '\033[46m'
    
    # Formatting
    RESET = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'

def print_user(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}🧑 You:{Colors.RESET} {text}")

def print_ai(text, model_name="Claude"):
    print(f"\n{Colors.BOLD}{Colors.GREEN}🤖 {model_name}:{Colors.RESET} {text}")

def print_tool(text):
    print(f"{Colors.YELLOW}🔧 {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ Error: {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.PURPLE}🔍 {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.PURPLE}{'='*60}{Colors.RESET}")

def print_divider():
    print(f"{Colors.DIM}{'-'*60}{Colors.RESET}")

class MCPClient:
    """Client for interacting with MCP Kali server"""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url
        self.enabled = False
        self.check_connection()
    
    def check_connection(self) -> bool:
        """Check if MCP server is running"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=2)
            self.enabled = response.status_code == 200
            return self.enabled
        except:
            self.enabled = False
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> dict:
        """Execute a command via MCP server"""
        if not self.enabled:
            return {"error": "MCP server not connected"}
        
        try:
            response = requests.post(
                f"{self.server_url}/api/command",
                json={"command": command},
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

class autohack:
    """Main CLI application"""
    
    def __init__(self, use_mcp: bool = False, mcp_server: str = "http://localhost:5000", model: str = "claude"):
        # Model configuration
        self.models = {
            "claude": {
                "name": "Claude",
                "api_key_env": "ANTHROPIC_API_KEY",
                "client": None,
                "available": True
            },
            "gpt": {
                "name": "GPT",
                "api_key_env": "OPENAI_API_KEY",
                "client": None,
                "available": openai is not None
            },
            "gemini": {
                "name": "Gemini",
                "api_key_env": "GOOGLE_API_KEY",
                "client": None,
                "available": genai is not None
            }
        }
        
        # Set current model
        self.current_model = model.lower()
        if self.current_model not in self.models:
            print_error(f"Invalid model: {model}. Using claude as default.")
            self.current_model = "claude"
        
        # Initialize clients
        self._initialize_clients()
        
        # Initialize MCP if requested
        self.mcp = None
        if use_mcp:
            self.mcp = MCPClient(mcp_server)
            if self.mcp.enabled:
                print_tool(f"MCP connected to {mcp_server} ✓")
            else:
                print_error(f"MCP server not available at {mcp_server}")
                print("Continuing without MCP. Start it with:")
                print("  Terminal 1: kali-server-mcp --port 5000")
                print("  Terminal 2: mcp-server --server http://localhost:5000")
        
        # Conversation history
        self.conversation = []
        
        # Workflow management
        self.workflows_dir = os.path.join(os.path.expanduser("~"), ".autohack", "workflows")
        os.makedirs(self.workflows_dir, exist_ok=True)
        self.workflows = self._load_workflows()
        self._init_predefined_workflows()
        
        # Command history
        self.history_file = os.path.join(os.path.expanduser("~"), ".autohack", "history.txt")
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        self._setup_history()
    
    def _initialize_clients(self):
        """Initialize AI model clients"""
        # Initialize Claude
        if self.models["claude"]["available"]:
            api_key = os.environ.get(self.models["claude"]["api_key_env"])
            if api_key:
                self.models["claude"]["client"] = anthropic.Anthropic(api_key=api_key)
            else:
                print_error(f"{self.models['claude']['api_key_env']} not found in environment")
                self.models["claude"]["available"] = False
        
        # Initialize GPT
        if self.models["gpt"]["available"]:
            api_key = os.environ.get(self.models["gpt"]["api_key_env"])
            if api_key:
                openai.api_key = api_key
                self.models["gpt"]["client"] = openai
            else:
                print_error(f"{self.models['gpt']['api_key_env']} not found in environment")
                self.models["gpt"]["available"] = False
        
        # Initialize Gemini
        if self.models["gemini"]["available"]:
            api_key = os.environ.get(self.models["gemini"]["api_key_env"])
            if api_key:
                genai.configure(api_key=api_key)
                self.models["gemini"]["client"] = genai
            else:
                print_error(f"{self.models['gemini']['api_key_env']} not found in environment")
                self.models["gemini"]["available"] = False
        
        # Ensure current model is available
        if not self.models[self.current_model]["available"]:
            # Fallback to first available model
            for model_name, model_info in self.models.items():
                if model_info["available"]:
                    print_error(f"Current model {self.current_model} not available. Falling back to {model_name}.")
                    self.current_model = model_name
                    break
            else:
                print_error("No AI models available. Exiting.")
                sys.exit(1)
    
    def _load_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load workflows from directory"""
        workflows = {}
        for filename in os.listdir(self.workflows_dir):
            if filename.endswith(".json"):
                workflow_name = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.workflows_dir, filename), "r") as f:
                        workflow_data = json.load(f)
                        workflows[workflow_name] = workflow_data
                except Exception as e:
                    print_error(f"Error loading workflow {workflow_name}: {e}")
        return workflows
    
    def _init_predefined_workflows(self):
        """Initialize predefined workflow templates"""
        predefined_workflows = {
            "reconnaissance": {
                "name": "Reconnaissance",
                "description": "Basic reconnaissance workflow",
                "steps": [
                    {"command": "nmap -sV -sC {target}", "description": "Scan target with Nmap"},
                    {"command": "whois {target}", "description": "Perform WHOIS lookup"},
                    {"command": "dig {target}", "description": "Perform DNS lookup"}
                ],
                "variables": ["target"]
            },
            "web_vulnerability_scan": {
                "name": "Web Vulnerability Scan",
                "description": "Web application vulnerability scanning workflow",
                "steps": [
                    {"command": "gobuster dir -u {target} -w /usr/share/wordlists/dirb/common.txt", "description": "Directory enumeration"},
                    {"command": "nikto -h {target}", "description": "Web server scanner"}
                ],
                "variables": ["target"]
            },
            "password_cracking": {
                "name": "Password Cracking",
                "description": "Password cracking workflow",
                "steps": [
                    {"command": "john --wordlist=/usr/share/wordlists/rockyou.txt {hash_file}", "description": "Crack hashes with John the Ripper"}
                ],
                "variables": ["hash_file"]
            }
        }
        
        for workflow_name, workflow_data in predefined_workflows.items():
            workflow_file = os.path.join(self.workflows_dir, f"{workflow_name}.json")
            if not os.path.exists(workflow_file):
                try:
                    with open(workflow_file, "w") as f:
                        json.dump(workflow_data, f, indent=2)
                    self.workflows[workflow_name] = workflow_data
                except Exception as e:
                    print_error(f"Error saving predefined workflow {workflow_name}: {e}")
    
    def _setup_history(self):
        """Setup command history and auto-completion"""
        # Set history file
        readline.set_history_length(1000)  # Limit history to 1000 entries
        
        # Load history if file exists
        if os.path.exists(self.history_file):
            try:
                readline.read_history_file(self.history_file)
            except Exception as e:
                print_error(f"Error loading history: {e}")
        
        # Setup auto-completion
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        
        # Save history on exit
        import atexit
        atexit.register(self._save_history)
    
    def _completer(self, text, state):
        """Command auto-completion function"""
        # List of available commands
        commands = [
            "runlocal", "runclaude", "model", "models", "workflows",
            "runworkflow", "createworkflow", "deleteworkflow", "menu",
            "quit", "exit", "clear"
        ]
        
        # Get available models
        model_names = [model_name for model_name, model_info in self.models.items() if model_info["available"]]
        
        # Get available workflows
        workflow_names = list(self.workflows.keys())
        
        # Split the current input to determine what to complete
        line = readline.get_line_buffer()
        parts = line.split()
        
        # If no parts yet, complete commands
        if not parts:
            matches = [cmd for cmd in commands if cmd.startswith(text)]
        else:
            # If first part is a command, complete based on command
            first_part = parts[0]
            if first_part == "model":
                # Complete model names
                matches = [model for model in model_names if model.startswith(text)]
            elif first_part == "runworkflow" or first_part == "deleteworkflow":
                # Complete workflow names
                matches = [wf for wf in workflow_names if wf.startswith(text)]
            else:
                # For other commands, complete with commands that start with text
                matches = [cmd for cmd in commands if cmd.startswith(text)]
        
        # Return the state-th match
        if state < len(matches):
            return matches[state]
        else:
            return None
    
    def _save_history(self):
        """Save command history to file"""
        try:
            readline.write_history_file(self.history_file)
        except Exception as e:
            print_error(f"Error saving history: {e}")
    
    def _save_workflow(self, name: str, workflow_data: Dict[str, Any]):
        """Save workflow to file"""
        try:
            workflow_file = os.path.join(self.workflows_dir, f"{name}.json")
            with open(workflow_file, "w") as f:
                json.dump(workflow_data, f, indent=2)
            self.workflows[name] = workflow_data
            return True
        except Exception as e:
            print_error(f"Error saving workflow {name}: {e}")
            return False
    
    def run_workflow(self, workflow_name: str, variables: Dict[str, str]):
        """Run a workflow"""
        if workflow_name not in self.workflows:
            return f"Error: Workflow '{workflow_name}' not found"
        
        workflow = self.workflows[workflow_name]
        results = []
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}🚀 Running workflow: {workflow['name']}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}📝 Description: {workflow['description']}{Colors.RESET}")
        
        for i, step in enumerate(workflow['steps'], 1):
            print(f"\n{Colors.BOLD}{Colors.BLUE}Step {i}: {step['description']}{Colors.RESET}")
            
            # Replace variables in command
            command = step['command']
            for var, value in variables.items():
                command = command.replace(f"{{{var}}}", value)
            
            print_tool(f"Executing: {command}")
            
            if self.mcp and self.mcp.enabled:
                result = self.run_command(command)
                results.append({"step": i, "command": command, "result": result})
                print(f"\n{Colors.BOLD}Output:{Colors.RESET}")
                print(result)
            else:
                print_error("MCP not connected. Cannot execute commands.")
                return "Error: MCP not connected"
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Workflow completed!{Colors.RESET}")
        return "Workflow completed successfully"
    
    def list_workflows(self):
        """List available workflows"""
        if not self.workflows:
            return "No workflows available"
        
        output = f"\n{Colors.BOLD}Available Workflows:{Colors.RESET}\n"
        for name, workflow in self.workflows.items():
            output += f"  • {name}: {workflow['name']} - {workflow['description']}\n"
        return output
    
    def create_workflow(self, name: str, workflow_data: Dict[str, Any]):
        """Create a new workflow"""
        if name in self.workflows:
            return f"Error: Workflow '{name}' already exists"
        
        if self._save_workflow(name, workflow_data):
            return f"Workflow '{name}' created successfully"
        else:
            return f"Error creating workflow '{name}'"
    
    def delete_workflow(self, name: str):
        """Delete a workflow"""
        if name not in self.workflows:
            return f"Error: Workflow '{name}' not found"
        
        try:
            workflow_file = os.path.join(self.workflows_dir, f"{name}.json")
            if os.path.exists(workflow_file):
                os.remove(workflow_file)
            del self.workflows[name]
            return f"Workflow '{name}' deleted successfully"
        except Exception as e:
            print_error(f"Error deleting workflow {name}: {e}")
            return f"Error deleting workflow '{name}'"
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"\n{Colors.BOLD}{Colors.GREEN}{'╔'+'═'*70+'╗'}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.CYAN}⚡ autohack - Interactive Menu ⚡{Colors.RESET}         {Colors.BOLD}{Colors.GREEN}║{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.GREEN}╠{'═'*70+'╣'}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.PURPLE}🤖 Current Model: {self.models[self.current_model]['name']}{Colors.RESET}           {Colors.BOLD}{Colors.GREEN}║{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.GREEN}╚{'═'*70+'╝'}{Colors.RESET}")
            
            print_section("Main Menu")
            
            menu_options = [
                ("1", "Execute a command locally", "runlocal"),
                ("2", "Execute command with AI analysis", "runclaude"),
                ("3", "Switch AI model", "model"),
                ("4", "List available AI models", "models"),
                ("5", "List available workflows", "workflows"),
                ("6", "Run a workflow", "runworkflow"),
                ("7", "Create a new workflow", "createworkflow"),
                ("8", "Delete a workflow", "deleteworkflow"),
                ("9", "Clear conversation history", "clear"),
                ("0", "Exit autohack", "exit")
            ]
            
            for option in menu_options:
                print(f"  {Colors.BOLD}{Colors.YELLOW}{option[0]}{Colors.RESET}. {option[1]}")
            
            print_divider()
            choice = input(f"{Colors.BOLD}{Colors.BLUE}Enter your choice (0-9):{Colors.RESET} ").strip()
            
            if choice == "0":
                print(f"\n{Colors.GREEN}👋 Exiting autohack. Every command teaches. Every mistake refines! 🔐{Colors.RESET}\n")
                sys.exit(0)
            
            selected_option = None
            for option in menu_options:
                if option[0] == choice:
                    selected_option = option
                    break
            
            if not selected_option:
                print_error("Invalid choice. Please try again.")
                input("Press Enter to continue...")
                continue
            
            # Handle menu option
            if selected_option[2] == "runlocal":
                command = input(f"{Colors.BOLD}{Colors.BLUE}Enter command to execute:{Colors.RESET} ").strip()
                if command:
                    if self.mcp and self.mcp.enabled:
                        result = self.run_command(command)
                        print(f"\n{Colors.BOLD}Output:{Colors.RESET}\n{result}")
                    else:
                        print_error("MCP not connected. Cannot execute commands.")
            
            elif selected_option[2] == "runclaude":
                command = input(f"{Colors.BOLD}{Colors.BLUE}Enter command to execute:{Colors.RESET} ").strip()
                if command:
                    if self.mcp and self.mcp.enabled:
                        print_tool(f"Executing: {command}")
                        result = self.run_command(command)
                        print(f"\n{Colors.BOLD}Command Output:{Colors.RESET}")
                        print(result)
                        print("")
                        enhanced_prompt = (
                            f"I just executed this command on my Kali Linux system:\n\n"
                            f"Command: {command}\n\n"
                            f"Output:\n{result}\n\n"
                            f"Please provide your analysis in sections:\n"
                            f"1. Summary of findings\n"
                            f"2. Key insights and observations\n"
                            f"3. Security implications (if any)\n"
                            f"4. Recommendations or next steps"
                        )
                        response = self.chat(enhanced_prompt)
                        print_ai(response, self.models[self.current_model]['name'])
                    else:
                        print_error("MCP not connected. Cannot execute commands.")
            
            elif selected_option[2] == "model":
                print_info("Available models: claude, gpt, gemini")
                model = input(f"{Colors.BOLD}{Colors.BLUE}Enter model name:{Colors.RESET} ").strip().lower()
                if model in self.models:
                    if self.models[model]["available"]:
                        self.current_model = model
                        self.conversation = []
                        print_success(f"Switched to {self.models[model]['name']} model")
                    else:
                        print_error(f"{self.models[model]['name']} model is not available. Check API key.")
                else:
                    print_error(f"Invalid model. Available models: {', '.join(self.models.keys())}")
            
            elif selected_option[2] == "models":
                print(f"\n{Colors.BOLD}Available AI Models:{Colors.RESET}")
                for model_name, model_info in self.models.items():
                    status = "✓" if model_info["available"] else "✗"
                    print(f"  • {model_name}: {model_info['name']} [{status}]")
                print(f"\nCurrent model: {self.current_model} ({self.models[self.current_model]['name']})")
            
            elif selected_option[2] == "workflows":
                print(self.list_workflows())
            
            elif selected_option[2] == "runworkflow":
                workflow_name = input(f"{Colors.BOLD}{Colors.BLUE}Enter workflow name:{Colors.RESET} ").strip()
                if workflow_name in self.workflows:
                    workflow = self.workflows[workflow_name]
                    variables = {}
                    for var in workflow.get("variables", []):
                        value = input(f"{Colors.BOLD}{Colors.BLUE}Enter value for {var}:{Colors.RESET} ").strip()
                        variables[var] = value
                    result = self.run_workflow(workflow_name, variables)
                    print(result)
                else:
                    print_error(f"Workflow '{workflow_name}' not found")
            
            elif selected_option[2] == "createworkflow":
                workflow_name = input(f"{Colors.BOLD}{Colors.BLUE}Enter workflow name:{Colors.RESET} ").strip()
                if workflow_name in self.workflows:
                    print_error(f"Workflow '{workflow_name}' already exists")
                else:
                    print_info("Enter workflow JSON (e.g.: {\"name\": \"Test\", \"description\": \"Test workflow\", \"steps\": [{\"command\": \"echo test\", \"description\": \"Test step\"}], \"variables\": []}")
                    json_input = input(f"{Colors.BOLD}{Colors.BLUE}Enter JSON:{Colors.RESET} ").strip()
                    try:
                        workflow_data = json.loads(json_input)
                        result = self.create_workflow(workflow_name, workflow_data)
                        print(result)
                    except json.JSONDecodeError:
                        print_error("Invalid JSON format")
            
            elif selected_option[2] == "deleteworkflow":
                workflow_name = input(f"{Colors.BOLD}{Colors.BLUE}Enter workflow name to delete:{Colors.RESET} ").strip()
                result = self.delete_workflow(workflow_name)
                print(result)
            
            elif selected_option[2] == "clear":
                self.conversation = []
                print_success("Conversation cleared.")
            
            input("\nPress Enter to return to menu...")
        
    def detect_command_request(self, text: str) -> Optional[str]:
        """Detect if user is asking to run a command"""
        text_lower = text.lower()
        
        # Direct command indicators
        if text_lower.startswith(("run ", "execute ", "exec ")):
            return text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        
        # Command-like patterns
        common_tools = ["nmap", "nikto", "gobuster", "dirb", "sqlmap", "hydra", 
                       "netcat", "nc", "curl", "wget", "dig", "whois"]
        
        first_word = text.split()[0] if text.split() else ""
        if first_word in common_tools:
            return text
        
        return None
    
    def run_command(self, command: str) -> str:
        """Execute command via MCP and return results"""
        if not self.mcp or not self.mcp.enabled:
            return f"Cannot execute command. MCP not connected.\nYou can run manually: {command}"
        
        print_tool(f"Executing: {command}")
        result = self.mcp.execute_command(command)
        
        if "error" in result:
            return f"Command failed: {result['error']}"
        
        # The Kali MCP server returns stdout, stderr, return_code
        output = result.get("stdout", "")
        errors = result.get("stderr", "")
        
        combined = ""
        if output:
            combined += output
        if errors:
            combined += f"\n[stderr]: {errors}"
        
        return combined if combined else str(result)
    
    def chat(self, user_message: str) -> str:
        """Send message to AI model and get response"""
        
        # Check if user wants to execute a command
        command = self.detect_command_request(user_message) if self.mcp else None
        
        if command:
            # Execute command and add results to context
            cmd_output = self.run_command(command)
            
            enhanced_message = f"{user_message}\n\nCommand output:\n```\n{cmd_output}\n```"
            self.conversation.append({
                "role": "user",
                "content": enhanced_message
            })
        else:
            self.conversation.append({
                "role": "user",
                "content": user_message
            })
        
        try:
            # Call appropriate AI model API
            if self.current_model == "claude":
                response = self.models["claude"]["client"].messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=self.conversation
                )
                assistant_message = response.content[0].text
            
            elif self.current_model == "gpt":
                response = self.models["gpt"]["client"].chat.completions.create(
                    model="gpt-4o",
                    max_tokens=4096,
                    messages=self.conversation
                )
                assistant_message = response.choices[0].message.content
            
            elif self.current_model == "gemini":
                # Convert conversation format for Gemini
                gemini_messages = []
                for msg in self.conversation:
                    if msg["role"] == "user":
                        gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                    else:
                        gemini_messages.append({"role": "model", "parts": [msg["content"]]})
                
                model = self.models["gemini"]["client"].GenerativeModel("gemini-1.5-flash")
                chat = model.start_chat(history=gemini_messages[:-1])  # Exclude last user message
                response = chat.send_message(gemini_messages[-1]["parts"][0])
                assistant_message = response.text
            
            else:
                return f"Error: Unknown model {self.current_model}"
            
            # Add to conversation history
            self.conversation.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
            
        except Exception as e:
            return f"Error calling {self.models[self.current_model]['name']} API: {e}"
    
    def run(self):
        """Main chat loop"""
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Welcome banner
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'╔'+'═'*70+'╗'}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.CYAN}⚡ autohack - AI Pentesting Assistant ⚡{Colors.RESET}         {Colors.BOLD}{Colors.GREEN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}╠{'═'*70+'╣'}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.BLUE}🚀 FULL FEATURES MODE{Colors.RESET}                                  {Colors.BOLD}{Colors.GREEN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.PURPLE}🤖 Current Model: {self.models[self.current_model]['name']}{Colors.RESET}           {Colors.BOLD}{Colors.GREEN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.YELLOW}👨‍💻 By: Christopher M. Burkett (CyberAndFires){Colors.RESET}      {Colors.BOLD}{Colors.GREEN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}╚{'═'*70+'╝'}{Colors.RESET}")
        
        print_divider()
        
        if self.mcp and self.mcp.enabled:
            print_success("MCP Mode: Commands will be executed automatically")
        else:
            print_warning("Manual Mode: I'll provide guidance only")
        
        # Show model availability
        available_models = [model_name for model_name, model_info in self.models.items() if model_info["available"]]
        if available_models:
            print_info(f"Available Models: {', '.join(available_models)}")
            print_info("Use 'model <name>' to switch, 'models' to list all")
        
        print_section("Available Commands")
        commands = [
            ("runlocal <command>", "Execute command locally without AI analysis"),
            ("runclaude <command>", "AI executes and analyzes the command"),
            ("model <model>", "Switch AI model (options: claude, gpt, gemini)"),
            ("models", "List available AI models"),
            ("workflows", "List available workflows"),
            ("runworkflow <name> <var1=value1>", "Run a workflow with variables"),
            ("createworkflow <name> <json>", "Create a new workflow"),
            ("deleteworkflow <name>", "Delete a workflow"),
            ("menu", "Show interactive menu"),
            ("quit or exit", "Leave autohack"),
            ("clear", "Clear conversation history")
        ]
        
        for cmd, desc in commands:
            print(f"  • {Colors.BOLD}{Colors.CYAN}{cmd}{Colors.RESET} - {desc}")
        
        print_section("Ready for Action")
        print_info("Type a command or ask a question to get started")
        
        while True:
            try:
                user_input = input(f"{Colors.BOLD}{Colors.BLUE}You:{Colors.RESET} ").strip()
                
                if not user_input:
                    continue
                
                # Handle runlocal command
                if user_input.lower().startswith("runlocal "):
                    command = user_input[9:].strip()
                    if self.mcp and self.mcp.enabled:
                        result = self.run_command(command)
                        print(f"\n{Colors.BOLD}Output:{Colors.RESET}\n{result}")
                    else:
                        print_error("MCP not connected. Cannot execute commands.")
                    continue
                
               # Handle runclaude command
                if user_input.lower().startswith("runclaude "):
                    command = user_input[10:].strip()
                    if self.mcp and self.mcp.enabled:
                        # Execute the command first
                        print_tool(f"Executing: {command}")
                        result = self.run_command(command)
                        
                        # Show the raw output
                        print(f"\n{Colors.BOLD}Command Output:{Colors.RESET}")
                        print(result)
                        print("")
                        
                        # Now ask AI to analyze
                        enhanced_prompt = (
                            f"I just executed this command on my Kali Linux system:\n\n"
                            f"Command: {command}\n\n"
                            f"Output:\n{result}\n\n"
                            f"Please provide your analysis in sections:\n"
                            f"1. Summary of findings\n"
                            f"2. Key insights and observations\n"
                            f"3. Security implications (if any)\n"
                            f"4. Recommendations or next steps"
                        )
                        response = self.chat(enhanced_prompt)
                        print_ai(response, self.models[self.current_model]['name'])
                    else:
                        print_error("MCP not connected. Cannot execute commands.")
                    continue
                
                # Handle model switching
                if user_input.lower().startswith("model "):
                    new_model = user_input[6:].strip().lower()
                    if new_model in self.models:
                        if self.models[new_model]["available"]:
                            old_model = self.current_model
                            self.current_model = new_model
                            self.conversation = []  # Clear conversation when switching models
                            print(f"{Colors.GREEN}✓ Switched to {self.models[new_model]['name']} model{Colors.RESET}")
                        else:
                            print_error(f"{self.models[new_model]['name']} model is not available. Check API key.")
                    else:
                        print_error(f"Invalid model. Available models: {', '.join(self.models.keys())}")
                    continue
                
                # List available models
                if user_input.lower() == 'models':
                    print(f"\n{Colors.BOLD}Available AI Models:{Colors.RESET}")
                    for model_name, model_info in self.models.items():
                        status = "✓" if model_info["available"] else "✗"
                        print(f"  • {model_name}: {model_info['name']} [{status}]")
                    print(f"\nCurrent model: {self.current_model} ({self.models[self.current_model]['name']})")
                    continue
                
                # List available workflows
                if user_input.lower() == 'workflows':
                    print(self.list_workflows())
                    continue
                
                # Run workflow
                if user_input.lower().startswith("runworkflow "):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print_error("Usage: runworkflow <name> <var1=value1> <var2=value2>")
                        continue
                    
                    workflow_parts = parts[1].split()
                    if not workflow_parts:
                        print_error("Usage: runworkflow <name> <var1=value1> <var2=value2>")
                        continue
                    
                    workflow_name = workflow_parts[0]
                    variables = {}
                    
                    # Parse variables
                    for var_part in workflow_parts[1:]:
                        if '=' in var_part:
                            var, value = var_part.split('=', 1)
                            variables[var] = value
                    
                    result = self.run_workflow(workflow_name, variables)
                    print(result)
                    continue
                
                # Create workflow
                if user_input.lower().startswith("createworkflow "):
                    parts = user_input.split(maxsplit=2)
                    if len(parts) < 3:
                        print_error("Usage: createworkflow <name> <json>")
                        continue
                    
                    workflow_name = parts[1]
                    try:
                        workflow_data = json.loads(parts[2])
                        result = self.create_workflow(workflow_name, workflow_data)
                        print(result)
                    except json.JSONDecodeError:
                        print_error("Invalid JSON format")
                    continue
                
                # Delete workflow
                if user_input.lower().startswith("deleteworkflow "):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print_error("Usage: deleteworkflow <name>")
                        continue
                    
                    workflow_name = parts[1]
                    result = self.delete_workflow(workflow_name)
                    print(result)
                    continue
                
                # Show interactive menu
                if user_input.lower() == 'menu':
                    self.show_menu()
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"\n{Colors.GREEN}👋 Exiting autohack. Every command teaches. Every mistake refines! 🔐{Colors.RESET}\n")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation = []
                    print(f"{Colors.YELLOW}Conversation cleared.{Colors.RESET}")
                    continue
                
                # Get AI response
                response = self.chat(user_input)
                print_ai(response, self.models[self.current_model]['name'])

            except KeyboardInterrupt:
                print(f"\n\n{Colors.GREEN}👋 Exiting autohack. Every command teaches. Every mistake refines! 🔐{Colors.RESET}\n")
                break
            except Exception as e:
                print_error(f"Unexpected error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="autohack - AI pentesting assistant with MCP integration"
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Enable MCP integration for command execution"
    )
    parser.add_argument(
        "--mcp-server",
        default="http://localhost:5000",
        help="MCP server URL (default: http://localhost:5000)"
    )
    parser.add_argument(
        "--model",
        default="claude",
        choices=["claude", "gpt", "gemini"],
        help="AI model to use (default: claude)"
    )
    
    args = parser.parse_args()
    
    app = autohack(use_mcp=args.mcp, mcp_server=args.mcp_server, model=args.model)
    app.run()

if __name__ == "__main__":
    main()
