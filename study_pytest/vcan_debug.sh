cat > vcan_debug.sh << 'EOF'
#!/bin/bash
# vcan問題デバッグ情報収集スクリプト
OUTPUT_FILE="vcan_debug_$(date +%Y%m%d_%H%M%S).txt"
echo "=== VCAN Debug Information ===" > $OUTPUT_FILE
echo "Generated: $(date)" >> $OUTPUT_FILE
echo "Host: $(hostname)" >> $OUTPUT_FILE
echo -e "\n=== WSL Environment ===" >> $OUTPUT_FILE
echo "Kernel: $(uname -a)" >> $OUTPUT_FILE
echo "Distribution: $(lsb_release -d 2>/dev/null || echo 'Unknown')" >> $OUTPUT_FILE
echo "WSL Version: $(cat /proc/version | grep -o 'Microsoft.*')" >> $OUTPUT_FILE
echo -e "\n=== VCAN Module Test ===" >> $OUTPUT_FILE
echo "Command: sudo modprobe vcan" >> $OUTPUT_FILE
sudo modprobe vcan >> $OUTPUT_FILE 2>&1
echo "Exit code: $?" >> $OUTPUT_FILE
echo -e "\n=== Module Search ===" >> $OUTPUT_FILE
echo "Searching for CAN modules..." >> $OUTPUT_FILE
find /lib/modules/$(uname -r) -name "*can*" 2>/dev/null >> $OUTPUT_FILE || echo "No CAN modules found" >> $OUTPUT_FILE
echo -e "\n=== Kernel Drivers ===" >> $OUTPUT_FILE
ls -la /lib/modules/$(uname -r)/kernel/drivers/net/ 2>/dev/null | grep can >> $OUTPUT_FILE || echo "No CAN drivers found" >> $OUTPUT_FILE
echo -e "\n=== dmesg CAN-related ===" >> $OUTPUT_FILE
dmesg | grep -i "can\|vcan\|module" | tail -20 >> $OUTPUT_FILE || echo "No CAN-related dmesg entries" >> $OUTPUT_FILE
echo -e "\n=== Loaded Modules ===" >> $OUTPUT_FILE
lsmod | grep can >> $OUTPUT_FILE || echo "No CAN modules loaded" >> $OUTPUT_FILE
echo -e "\n=== Kernel Config ===" >> $OUTPUT_FILE
if [ -f /proc/config.gz ]; then
     zcat /proc/config.gz | grep -E "CONFIG_CAN|CONFIG_VCAN" >> $OUTPUT_FILE
else
     echo "Kernel config not available" >> $OUTPUT_FILE
fi
echo -e "\n=== Package Information ===" >> $OUTPUT_FILE
dpkg -l | grep -E "can-utils|linux-modules" >> $OUTPUT_FILE || echo "No relevant packages found" >> $OUTPUT_FILE
echo -e "\n=== Network Interfaces ===" >> $OUTPUT_FILE
ip link show >> $OUTPUT_FILE 2>&1
echo "Debug information saved to: $OUTPUT_FILE"
echo "Location: $(pwd)/$OUTPUT_FILE"
EOF