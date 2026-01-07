"""
G-Code Style Command Parser

Parses simple text commands into structured format for execution.
Supports commands like: pointer 200 200, click 2 s, type "hello", etc.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CommandParser:
    """Parse G-code style commands into structured format."""
    
    def __init__(self):
        self.command_patterns = {
            'pointer': r'pointer\s+(\d+)\s+(\d+)',
            'click': r'click\s+(\d+)\s+([sd])',  # button clicks (s=single, d=double)
            'type': r'type\s+"([^"]+)"',  # type "text"
            'key': r'key\s+(\S+)',  # key Return, key Tab, etc.
            'wait': r'wait\s+([\d.]+)',  # wait 1.5
            'drag': r'drag\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',  # drag x1 y1 x2 y2 duration
            'scroll': r'scroll\s+(\d+)\s+(\d+)\s+([-\d]+)',  # scroll x y amount
            'swipe': r'swipe\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',  # swipe x1 y1 x2 y2 duration
            'multiclick': r'multiclick\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',  # multiclick x y count delay
            'keycombo': r'keycombo\s+"([^"]+)"',  # keycombo "Ctrl+Shift+T"
            'waitfor': r'waitfor\s+window\s+"([^"]+)"\s+(\d+)',  # waitfor window "Firefox" 10
            'screenshot': r'screenshot\s+"([^"]+)"',  # screenshot "filename"
        }
    
    def parse(self, command_text: str) -> List[Dict[str, Any]]:
        """
        Parse G-code style command text into structured commands.
        
        Args:
            command_text: Multi-line string with commands
            
        Returns:
            List of command dictionaries
        """
        commands = []
        lines = command_text.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments
            
            command = self._parse_line(line, line_num)
            if command:
                commands.append(command)
            else:
                logger.warning(f"Could not parse line {line_num}: {line}")
        
        return commands
    
    def _parse_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single line into a command dictionary."""
        line_lower = line.lower().strip()
        
        # Try each command pattern
        for action, pattern in self.command_patterns.items():
            match = re.match(pattern, line_lower, re.IGNORECASE)
            if match:
                return self._build_command(action, match, line)
        
        # Check for advanced commands (ifexists, loop, var)
        if line_lower.startswith('ifexists'):
            return self._parse_ifexists(line, line_num)
        elif line_lower.startswith('loop'):
            return self._parse_loop(line, line_num)
        elif '=' in line and line_lower.startswith('var'):
            return self._parse_var(line, line_num)
        
        return None
    
    def _build_command(self, action: str, match: re.Match, original_line: str) -> Dict[str, Any]:
        """Build command dictionary from regex match."""
        groups = match.groups()
        cmd = {"action": action, "original": original_line}
        
        if action == 'pointer':
            cmd['x'] = int(groups[0])
            cmd['y'] = int(groups[1])
        elif action == 'click':
            cmd['button'] = int(groups[0])  # 1=left, 2=middle, 3=right
            cmd['clicks'] = 'single' if groups[1] == 's' else 'double'
        elif action == 'type':
            cmd['text'] = groups[0]
        elif action == 'key':
            # Preserve original key name (case-sensitive for xdotool)
            # Extract from original line to preserve case
            key_match = re.search(r'key\s+(\S+)', original_line, re.IGNORECASE)
            if key_match:
                cmd['key'] = key_match.group(1)  # Preserve original case
            else:
                cmd['key'] = groups[0]
        elif action == 'wait':
            cmd['seconds'] = float(groups[0])
        elif action == 'drag':
            cmd['x1'] = int(groups[0])
            cmd['y1'] = int(groups[1])
            cmd['x2'] = int(groups[2])
            cmd['y2'] = int(groups[3])
            cmd['duration'] = float(groups[4])
        elif action == 'scroll':
            cmd['x'] = int(groups[0])
            cmd['y'] = int(groups[1])
            cmd['amount'] = int(groups[2])
        elif action == 'swipe':
            cmd['x1'] = int(groups[0])
            cmd['y1'] = int(groups[1])
            cmd['x2'] = int(groups[2])
            cmd['y2'] = int(groups[3])
            cmd['duration'] = float(groups[4])
        elif action == 'multiclick':
            cmd['x'] = int(groups[0])
            cmd['y'] = int(groups[1])
            cmd['count'] = int(groups[2])
            cmd['delay'] = float(groups[3])
        elif action == 'keycombo':
            cmd['combo'] = groups[0]
        elif action == 'waitfor':
            cmd['window'] = groups[0]
            cmd['timeout'] = int(groups[1])
        elif action == 'screenshot':
            cmd['filename'] = groups[0]
        
        return cmd
    
    def _parse_ifexists(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse ifexists command: ifexists "text" then action"""
        # Simple implementation - can be extended
        match = re.match(r'ifexists\s+"([^"]+)"\s+then\s+(.+)', line, re.IGNORECASE)
        if match:
            return {
                "action": "ifexists",
                "text": match.group(1),
                "then_action": match.group(2),
                "original": line
            }
        return None
    
    def _parse_loop(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse loop command: loop count { commands }"""
        # Simple implementation - can be extended
        match = re.match(r'loop\s+(\d+)\s+\{(.+)\}', line, re.IGNORECASE | re.DOTALL)
        if match:
            return {
                "action": "loop",
                "count": int(match.group(1)),
                "commands": match.group(2).strip(),
                "original": line
            }
        return None
    
    def _parse_var(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse var command: var name = value"""
        match = re.match(r'var\s+(\w+)\s*=\s*(.+)', line, re.IGNORECASE)
        if match:
            return {
                "action": "var",
                "name": match.group(1),
                "value": match.group(2).strip(),
                "original": line
            }
        return None
    
    def to_gcode(self, commands: List[Dict[str, Any]]) -> str:
        """
        Convert structured commands back to G-code text format.
        
        Args:
            commands: List of command dictionaries
            
        Returns:
            G-code text string
        """
        lines = []
        for cmd in commands:
            action = cmd.get('action')
            original = cmd.get('original', '')
            
            if original:
                lines.append(original)
            else:
                # Reconstruct from command dict
                line = self._command_to_line(cmd)
                if line:
                    lines.append(line)
        
        return '\n'.join(lines)
    
    def _command_to_line(self, cmd: Dict[str, Any]) -> str:
        """Convert command dict back to G-code line."""
        action = cmd.get('action')
        
        if action == 'pointer':
            return f"pointer {cmd['x']} {cmd['y']}"
        elif action == 'click':
            clicks = 's' if cmd.get('clicks') == 'single' else 'd'
            return f"click {cmd['button']} {clicks}"
        elif action == 'type':
            return f'type "{cmd["text"]}"'
        elif action == 'key':
            return f"key {cmd['key']}"
        elif action == 'wait':
            return f"wait {cmd['seconds']}"
        elif action == 'drag':
            return f"drag {cmd['x1']} {cmd['y1']} {cmd['x2']} {cmd['y2']} {cmd['duration']}"
        elif action == 'scroll':
            return f"scroll {cmd['x']} {cmd['y']} {cmd['amount']}"
        elif action == 'screenshot':
            return f'screenshot "{cmd["filename"]}"'
        else:
            return cmd.get('original', '')

