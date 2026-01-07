package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// Command represents a parsed command
type Command struct {
	Action   string                 `json:"action"`
	Params   map[string]interface{} `json:"params,omitempty"`
	Original string                 `json:"original,omitempty"`
}

// ExecutionResult represents the result of executing commands
type ExecutionResult struct {
	Status          string      `json:"status"`
	CommandsExecuted int        `json:"commands_executed"`
	Screenshots     []Screenshot `json:"screenshots"`
	Errors          []string    `json:"errors"`
}

// Screenshot represents a screenshot taken after an action
type Screenshot struct {
	Step   int    `json:"step"`
	File   string `json:"file"`
	Action string `json:"action"`
}

var screenshotsDir = "/tmp/cosmic-screenshots"
var screenshotCounter = 0

func main() {
	// Create screenshots directory
	os.MkdirAll(screenshotsDir, 0755)

	// Check for command line arguments
	if len(os.Args) > 1 {
		// Read from file
		if os.Args[1] == "--screenshots-dir" && len(os.Args) > 2 {
			screenshotsDir = os.Args[2]
			os.MkdirAll(screenshotsDir, 0755)
			if len(os.Args) > 3 {
				executeFromFile(os.Args[3])
			} else {
				executeFromStdin()
			}
		} else {
			executeFromFile(os.Args[1])
		}
	} else {
		// Read from stdin
		executeFromStdin()
	}
}

func executeFromFile(filename string) {
	file, err := os.Open(filename)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error opening file: %v\n", err)
		os.Exit(1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	executeCommands(scanner)
}

func executeFromStdin() {
	scanner := bufio.NewScanner(os.Stdin)
	executeCommands(scanner)
}

func executeCommands(scanner *bufio.Scanner) {
	result := ExecutionResult{
		Status:          "success",
		CommandsExecuted: 0,
		Screenshots:     []Screenshot{},
		Errors:          []string{},
	}

	step := 0
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue // Skip empty lines and comments
		}

		step++
		cmd := parseCommand(line)
		if cmd == nil {
			result.Errors = append(result.Errors, fmt.Sprintf("Step %d: Could not parse: %s", step, line))
			continue
		}

		// Execute command
		err := executeCommand(cmd)
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("Step %d: %v", step, err))
			result.Status = "error"
		} else {
			result.CommandsExecuted++
		}

		// Take screenshot after action (for verification)
		screenshotFile := takeScreenshot(step, cmd.Action)
		if screenshotFile != "" {
			result.Screenshots = append(result.Screenshots, Screenshot{
				Step:   step,
				File:   screenshotFile,
				Action: cmd.Action,
			})
		}
	}

	// Output result as JSON
	jsonOutput, _ := json.MarshalIndent(result, "", "  ")
	fmt.Println(string(jsonOutput))
}

func parseCommand(line string) *Command {
	parts := strings.Fields(line)
	if len(parts) == 0 {
		return nil
	}

	action := strings.ToLower(parts[0])
	cmd := &Command{
		Action:   action,
		Params:   make(map[string]interface{}),
		Original: line,
	}

	switch action {
	case "pointer":
		if len(parts) >= 3 {
			x, _ := strconv.Atoi(parts[1])
			y, _ := strconv.Atoi(parts[2])
			cmd.Params["x"] = x
			cmd.Params["y"] = y
			return cmd
		}
	case "click":
		if len(parts) >= 3 {
			button, _ := strconv.Atoi(parts[1])
			clicks := parts[2]
			cmd.Params["button"] = button
			cmd.Params["clicks"] = clicks
			return cmd
		}
	case "type":
		// Extract text in quotes
		text := strings.TrimPrefix(line, "type ")
		text = strings.Trim(text, "\"")
		cmd.Params["text"] = text
		return cmd
	case "key":
		if len(parts) >= 2 {
			cmd.Params["key"] = parts[1]
			return cmd
		}
	case "wait":
		if len(parts) >= 2 {
			seconds, _ := strconv.ParseFloat(parts[1], 64)
			cmd.Params["seconds"] = seconds
			return cmd
		}
	case "drag":
		if len(parts) >= 6 {
			x1, _ := strconv.Atoi(parts[1])
			y1, _ := strconv.Atoi(parts[2])
			x2, _ := strconv.Atoi(parts[3])
			y2, _ := strconv.Atoi(parts[4])
			duration, _ := strconv.ParseFloat(parts[5], 64)
			cmd.Params["x1"] = x1
			cmd.Params["y1"] = y1
			cmd.Params["x2"] = x2
			cmd.Params["y2"] = y2
			cmd.Params["duration"] = duration
			return cmd
		}
	case "scroll":
		if len(parts) >= 4 {
			x, _ := strconv.Atoi(parts[1])
			y, _ := strconv.Atoi(parts[2])
			amount, _ := strconv.Atoi(parts[3])
			cmd.Params["x"] = x
			cmd.Params["y"] = y
			cmd.Params["amount"] = amount
			return cmd
		}
	case "screenshot":
		if len(parts) >= 2 {
			filename := strings.Trim(parts[1], "\"")
			cmd.Params["filename"] = filename
			return cmd
		}
	}

	return nil
}

func executeCommand(cmd *Command) error {
	switch cmd.Action {
	case "pointer":
		x := int(cmd.Params["x"].(int))
		y := int(cmd.Params["y"].(int))
		return runXdotool("mousemove", strconv.Itoa(x), strconv.Itoa(y))

	case "click":
		button := int(cmd.Params["button"].(int))
		clicks := cmd.Params["clicks"].(string)
		
		// Get current mouse position or use coordinates if provided
		if x, ok := cmd.Params["x"]; ok {
			// Click at specific coordinates
			xVal := int(x.(int))
			yVal := int(cmd.Params["y"].(int))
			runXdotool("mousemove", strconv.Itoa(xVal), strconv.Itoa(yVal))
		}
		
		if clicks == "d" || clicks == "double" {
			// Double click
			runXdotool("click", "--repeat", "2", strconv.Itoa(button))
		} else {
			// Single click
			runXdotool("click", strconv.Itoa(button))
		}
		return nil

	case "type":
		text := cmd.Params["text"].(string)
		// Escape special characters for xdotool
		text = strings.ReplaceAll(text, "\"", "\\\"")
		return runXdotool("type", "--delay", "50", text)

	case "key":
		key := cmd.Params["key"].(string)
		return runXdotool("key", key)

	case "wait":
		seconds := cmd.Params["seconds"].(float64)
		time.Sleep(time.Duration(seconds * float64(time.Second)))
		return nil

	case "drag":
		x1 := int(cmd.Params["x1"].(int))
		y1 := int(cmd.Params["y1"].(int))
		x2 := int(cmd.Params["x2"].(int))
		y2 := int(cmd.Params["y2"].(int))
		duration := cmd.Params["duration"].(float64)
		
		// Move to start, press button, move to end, release
		runXdotool("mousemove", strconv.Itoa(x1), strconv.Itoa(y1))
		runXdotool("mousedown", "1")
		
		// Smooth drag over duration
		steps := int(duration * 10) // 10 steps per second
		if steps < 1 {
			steps = 1
		}
		dx := float64(x2-x1) / float64(steps)
		dy := float64(y2-y1) / float64(steps)
		stepDuration := time.Duration(duration * float64(time.Second) / float64(steps))
		
		for i := 0; i < steps; i++ {
			px := x1 + int(float64(i)*dx)
			py := y1 + int(float64(i)*dy)
			runXdotool("mousemove", strconv.Itoa(px), strconv.Itoa(py))
			time.Sleep(stepDuration)
		}
		
		runXdotool("mousemove", strconv.Itoa(x2), strconv.Itoa(y2))
		runXdotool("mouseup", "1")
		return nil

	case "scroll":
		x := int(cmd.Params["x"].(int))
		y := int(cmd.Params["y"].(int))
		amount := int(cmd.Params["amount"].(int))
		
		runXdotool("mousemove", strconv.Itoa(x), strconv.Itoa(y))
		// Scroll: 4 = up, 5 = down
		button := "4"
		if amount > 0 {
			button = "5" // Scroll down
		} else {
			amount = -amount // Make positive for repeat count
		}
		runXdotool("click", "--repeat", strconv.Itoa(amount), button)
		return nil

	case "screenshot":
		// Screenshot is handled separately in takeScreenshot
		return nil

	default:
		return fmt.Errorf("unknown action: %s", cmd.Action)
	}
}

func runXdotool(args ...string) error {
	cmd := exec.Command("xdotool", args...)
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func takeScreenshot(step int, action string) string {
	screenshotCounter++
	filename := fmt.Sprintf("screenshot_%d_%s_%d.png", step, action, screenshotCounter)
	filepath := filepath.Join(screenshotsDir, filename)
	
	// Use mss or import command (if available)
	// For now, use import (ImageMagick) as fallback, or xdotool screenshot if available
	// Try import first (ImageMagick)
	cmd := exec.Command("import", "-window", "root", filepath)
	if err := cmd.Run(); err == nil {
		return filepath
	}
	
	// Try xwd + convert (X11)
	cmd = exec.Command("xwd", "-root", "-out", filepath+".xwd")
	if err := cmd.Run(); err == nil {
		// Convert xwd to png
		convertCmd := exec.Command("convert", filepath+".xwd", filepath)
		if convertCmd.Run() == nil {
			os.Remove(filepath + ".xwd")
			return filepath
		}
		os.Remove(filepath + ".xwd")
	}
	
	// If all else fails, return empty (screenshot not available)
	return ""
}

