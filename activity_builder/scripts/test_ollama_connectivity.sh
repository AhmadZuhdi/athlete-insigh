#!/bin/bash
# Quick Ollama connectivity test script

echo "🔍 Testing Ollama connectivity from container..."
echo "================================================="

# Convert hex gateway to decimal IP
gateway_hex="0100590A"
# This is 10.89.1.1 in decimal

# Test various IP addresses that might be the Windows host
test_ips=(
    "192.168.1.70"
    "10.89.1.1"    # Converted gateway
    "10.89.0.1"    # Common Podman gateway
    "172.17.0.1"   # Docker default
    "192.168.1.1"  # Common router IP
    "host.containers.internal"
    "host.docker.internal"
    "localhost"
)

echo "Testing Ollama on port 11434..."
echo ""

for ip in "${test_ips[@]}"; do
    echo -n "Testing $ip:11434 ... "
    if timeout 3 bash -c "</dev/tcp/$ip/11434" 2>/dev/null; then
        echo "✅ Port is open!"
        echo "Trying API call..."
        if curl -s -m 3 "http://$ip:11434/api/tags" | grep -q "models"; then
            echo "🎉 Ollama API is working at $ip:11434"
            echo ""
            echo "💡 Update your .env file with:"
            echo "OLLAMA_HOST=$ip"
            exit 0
        else
            echo "⚠️  Port open but API not responding"
        fi
    else
        echo "❌ Cannot connect"
    fi
done

echo ""
echo "❌ Ollama not accessible from container"
echo ""
echo "🔧 To fix this:"
echo "1. On Windows, stop Ollama: taskkill /f /im ollama.exe"
echo "2. Start with network access: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve"
echo "3. Check Windows Firewall settings for port 11434"
