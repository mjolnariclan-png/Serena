import os
import subprocess
import tempfile
import platform
import sys
from pathlib import Path

def execute_code(code: str, language: str = "python") -> str:
    """
    Execute code snippet and return the result.
    Supports Python by default, can be extended for other languages.
    """
    if language.lower() != "python":
        return f"Sorry, I currently only support Python execution. Language: {language}"
    
    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout if result.stdout else "No output"
            error = result.stderr if result.stderr else ""
            
            if result.returncode != 0:
                return f"Execution failed:\n{error}"
            
            return f"Output:\n{output}"
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return "Code execution timed out (10 second limit)"
    except Exception as e:
        return f"Error executing code: {str(e)}"

def analyze_file(file_path: str) -> str:
    """
    Analyze a code file and provide insights.
    """
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic analysis
        lines = content.split('\n')
        total_lines = len(lines)
        non_empty_lines = [line for line in lines if line.strip()]
        code_lines = len(non_empty_lines)
        
        # Count common patterns
        imports = len([line for line in lines if line.strip().startswith('import') or line.strip().startswith('from')])
        functions = len([line for line in lines if 'def ' in line])
        classes = len([line for line in lines if 'class ' in line])
        
        analysis = f"""File analysis for {file_path}:
• Total lines: {total_lines}
• Code lines: {code_lines}
• Import statements: {imports}
• Functions: {functions}
• Classes: {classes}

This is a basic analysis. For more detailed code review, let me know what specific aspects you'd like me to focus on."""
        
        return analysis
        
    except Exception as e:
        return f"Error analyzing file: {str(e)}"

def create_project_structure(project_name: str, structure: str) -> str:
    """
    Create a project structure based on a text description.
    Simple format: "folder1/file1.py, folder1/file2.py, folder2/subfolder/file3.py"
    """
    try:
        base_path = Path(project_name)
        base_path.mkdir(exist_ok=True)
        
        files = [f.strip() for f in structure.split(',')]
        created_files = []
        
        for file_path in files:
            full_path = base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not full_path.suffix:  # It's a directory
                full_path.mkdir(exist_ok=True)
                created_files.append(f"Directory: {file_path}")
            else:  # It's a file
                full_path.touch()
                created_files.append(f"File: {file_path}")
        
        return f"Created project '{project_name}' with:\n" + "\n".join(created_files)
        
    except Exception as e:
        return f"Error creating project structure: {str(e)}"

def install_package(package_name: str) -> str:
    """
    Install a Python package using pip.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return f"Successfully installed {package_name}"
        else:
            return f"Failed to install {package_name}:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return f"Installation timed out for {package_name}"
    except Exception as e:
        return f"Error installing package: {str(e)}"

def is_coding_request(text: str) -> bool:
    """
    Check if the request is coding-related.
    """
    coding_keywords = [
        "execute", "run code", "test code", "analyze file",
        "create project", "install package", "debug",
        "code review", "optimize code"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in coding_keywords)

def handle_coding_request(text: str) -> str:
    """
    Handle various coding-related requests.
    """
    text_lower = text.lower()
    
    # Code execution
    if "execute" in text_lower or "run code" in text_lower:
        # Extract code between backticks or after certain keywords
        if "```" in text:
            code_start = text.find("```") + 3
            code_end = text.find("```", code_start)
            if code_end != -1:
                code = text[code_start:code_end].strip()
                language = "python"  # Default to Python
                if code_start > 3:
                    lang_spec = text[:code_start].split()[-1]
                    if lang_spec in ["python", "javascript", "java", "cpp"]:
                        language = lang_spec
                return execute_code(code, language)
        return "Please provide the code to execute. Format: ```python\nyour code here```"
    
    # File analysis
    if "analyze file" in text_lower:
        # Extract file path
        words = text_lower.split()
        if "analyze file" in text_lower:
            idx = text_lower.index("analyze file")
            file_path = text[idx + 12:].strip()
            return analyze_file(file_path)
    
    # Project creation
    if "create project" in text_lower:
        # Extract project name and structure
        idx = text_lower.index("create project")
        rest = text[idx + 14:].strip()
        parts = rest.split(maxsplit=1)
        if len(parts) >= 2:
            project_name = parts[0]
            structure = parts[1]
            return create_project_structure(project_name, structure)
        return "Please specify project name and structure. Format: create project myproject folder1/file1.py, folder2/file2.py"
    
    # Package installation
    if "install" in text_lower and "package" in text_lower:
        words = text_lower.split()
        try:
            package_idx = words.index("package") + 1
            if package_idx < len(words):
                package_name = words[package_idx]
                return install_package(package_name)
        except:
            pass
        return "Please specify the package name. Format: install package package_name"
    
    return None