#!/bin/bash
DEVIMAGE_DIR=$PWD/devimage-buster
DEVIMAGE_NAME=xmrsigner-dev.img
DEVIMAGE_MOUNT_BOOT=/mnt/xmrsignerdev_boot
DEVIMAGE_MOUNT_ROOT=/mnt/xmrsignerdev_root
IMAGE_URL='https://downloads.raspberrypi.org/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2023-05-03/2023-05-03-raspios-buster-armhf-lite.img.xz'
IMAGE_XZ_SHA256="3d210e61b057de4de90eadb46e28837585a9b24247c221998f5bead04f88624c"
HOSTNAME=xmrsigner-dev
USER=xmrsigner
USER_ID=1000
PASSWORD=$(openssl passwd -6 "xmrsigner" | sed -e 's/\//\\\//g')
SSH_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOehLkdqEEaaXBrv2ooTE92+jbC/b3Wrvp+R3b9HnSS9"
SSID=xmrsigner
NETWORK_PASSWORD=$(openssl passwd -5 "xmrsigner")
MONERO_WALLET_RPC_XMRSIGNER_VERSION=0.18.3.3-xmrsigner
MONERO_WALLET_RPC_XMRSIGNER_SOURCE=monero-wallet-rpc_linux_armv6_static.tar.bz2
MONERO_WALLET_RPC_XMRSIGNER_URL=https://github.com/DiosDelRayo/monero/releases/download/v${MONERO_WALLET_RPC_XMRSIGNER_VERSION}/${MONERO_WALLET_RPC_XMRSIGNER_SOURCE}
MONERO_WALLET_RPC_XMRSIGNER_SHA256="210fcc9f2f0fd255d9c58ab1f907237b8f3e86e108f55ed12bfc989ff1cfb74a"
MONERO_WALLET_RPC="monero-wallet-rpc"

set -e

get_monero_wallet_rpc() {
	if [ -f ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC} ]; then
		return
	fi
	wget -c -O $DEVIMAGE_DIR/monero-wallet-rpc.tar.bz2 "$MONERO_WALLET_RPC_XMRSIGNER_URL"
	echo -n "Check sha256 of ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2 download..."
	hash=$(sha256sum ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2 | awk '{ print $1 }')
	if [ "$hash" != "${MONERO_WALLET_RPC_XMRSIGNER_SHA256}" ]; then
		echo 'failed'
		exit 1
	else
		echo 'OK'
	fi
	echo "Extract ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2..."
	tar -C ${DEVIMAGE_DIR} -xjf ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2
	if [ -f "${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}" ] && [ -f "${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2" ]; then
		echo "Remove ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2..."
		rm -f ${DEVIMAGE_DIR}/${MONERO_WALLET_RPC}.tar.bz2
	fi
}

check_sudo() {
    if [ "$(id -u)" -ne 0 ]; then
	echo -e "\nThis script requires sudo privileges..."
	sudo true
	if [ $? -ne 0 ]
	then
	    echo "This script requires sudo privileges, but failed to aquire..."
	    exit 1
	fi
    fi
}

download_pios_image() {
    if [ ! -f $DEVIMAGE_DIR/raspios-lite.img ]
    then
	# Download the latest Raspberry Pi OS Lite image
	mkdir -p $DEVIMAGE_DIR
	echo 'Download RaspiOS lite image...'
	wget -c -O $DEVIMAGE_DIR/raspios-lite.img.xz "$IMAGE_URL"
	echo 'Check sha256 of compressed image against expected hash...'
	SHA256=$(sha256sum $DEVIMAGE_DIR/raspios-lite.img.xz | awk '{ print $1}')
	if [ "$IMAGE_XZ_SHA256" = "$SHA256" ]; then
	    echo 'Extract RaspiOS lite image...'
	    xz -d $DEVIMAGE_DIR/raspios-lite.img.xz
	else
	    echo "SHA256 checksum wrong! Delete $DEVIMAGE_DIR/raspios-lite.img.xz and try again."
	    exit 1
	fi
    fi
}

modify_image() {
    LOOP_DEVICE=$(sudo losetup -Pf --show $DEVIMAGE_DIR/$DEVIMAGE_NAME)

    sudo mkdir -p $DEVIMAGE_MOUNT_BOOT
    sudo mkdir -p $DEVIMAGE_MOUNT_ROOT

    # Mount partitions
    sudo mount "${LOOP_DEVICE}p1" $DEVIMAGE_MOUNT_BOOT
    sudo mount "${LOOP_DEVICE}p2" $DEVIMAGE_MOUNT_ROOT

    # Enable USB OTG
    echo "dtoverlay=dwc2" | sudo sh -c "cat >> ${DEVIMAGE_MOUNT_BOOT}/config.txt"
    sudo sed -i 's/#dtparam=spi=on/dtparam=spi=on/' $DEVIMAGE_MOUNT_BOOT/cmdline.txt
    sudo sed -i 's/rootwait/rootwait modules-load=dwc2,g_ether spidev.bufsiz=131072/' $DEVIMAGE_MOUNT_BOOT/cmdline.txt
    echo 'gpu_mem=128' | sudo sh -c "cat >> ${DEVIMAGE_MOUNT_BOOT}/config.txt"

    # rename user pi to xmrsigner, change password and add ssh key
    sudo sed -i "s/:pi/:${USER}/" $DEVIMAGE_MOUNT_ROOT/etc/group
    sudo sed -i "s/^pi:x:${USER_ID}/${USER}:x:${USER_ID}/" $DEVIMAGE_MOUNT_ROOT/etc/group
    sudo sed -i "s/^pi:/${USER}:/" $DEVIMAGE_MOUNT_ROOT/etc/passwd
    sudo sed -i "s/:\/home\/pi:/:\/home\/${USER}:/" $DEVIMAGE_MOUNT_ROOT/etc/passwd
    sudo sed -i "s/pi:\$6\$[^:]*:/xmrsigner:${PASSWORD}:/" $DEVIMAGE_MOUNT_ROOT/etc/shadow
    sudo mv $DEVIMAGE_MOUNT_ROOT/home/{pi,${USER}}
    sudo mkdir -p ${DEVIMAGE_MOUNT_ROOT}/home/${USER}/.ssh
    echo "${SSH_KEY}" | sudo sh -c "cat > ${DEVIMAGE_MOUNT_ROOT}/home/${USER}/.ssh/authorized_keys"
    sudo chown -R ${USER_ID}:${USER_ID} ${DEVIMAGE_MOUNT_ROOT}/home/${USER}/.ssh

    # copy monero-wallet-rpc
    sudo cp $DEVIMAGE_DIR/${MONERO_WALLET_RPC} $DEVIMAGE_MOUNT_ROOT/usr/bin/${MONERO_WALLET_RPC}
    sudo chmod u+x $DEVIMAGE_MOUNT_ROOT/usr/bin/${MONERO_WALLET_RPC}
    sudo chown ${USER_ID}:${USER_ID} $DEVIMAGE_MOUNT_ROOT/usr/bin/${MONERO_WALLET_RPC}

    # enable ssh
    sudo touch $DEVIMAGE_MOUNT_BOOT/ssh

#    echo 'Setup usb0 network interface...'
#    cat << 'EOF' | sudo sh -c "cat > ${DEVIMAGE_MOUNT_ROOT}/etc/network/interfaces.d/usb0"
#allow-hotplug usb0
#iface usb0 inet dhcp
#EOF

echo 'Creating XmrSigner service...'
cat << 'EOS' | sudo sh -c "cat > ${DEVIMAGE_MOUNT_ROOT}/etc/systemd/system/xmrsigner.service"
[Unit]
Description=XmrSigner

[Service]
User=${USER}
WorkingDirectory=/opt/xmrsigner
ExecStart=/bin/bash -c 'source /opt/xmrsigner/bin/activate && /usr/bin/python3 -m xmrsigner >> /var/log/xmrsigner.log 2>&1'
Restart=always

[Install]
WantedBy=multi-user.target
EOS

sudo touch ${DEVIMAGE_MOUNT_ROOT}/var/log/xmrsigner.log
sudo chown ${USER_ID}:${USER_ID} ${DEVIMAGE_MOUNT_ROOT}/var/log/xmrsigner.log
sudo chmod 644 ${DEVIMAGE_MOUNT_ROOT}/var/log/xmrsigner.log
sudo ln -s ${DEVIMAGE_MOUNT_ROOT}/etc/systemd/system/xmrsigner.service ${DEVIMAGE_MOUNT_ROOT}/etc/systemd/system/multi-user.target.wants/xmrsigner.service

    # Unmount the image
    sudo umount $DEVIMAGE_MOUNT_BOOT
    sudo umount $DEVIMAGE_MOUNT_ROOT
    sudo losetup -d "$LOOP_DEVICE"
    sudo rmdir $DEVIMAGE_MOUNT_BOOT
    sudo rmdir $DEVIMAGE_MOUNT_ROOT
}

create_image() {
    # Create and modify the image
    if [ -f $DEVIMAGE_DIR/$DEVIMAGE_NAME ] && [ "$1" != "--force" ]; then
	echo "Custom image already exists. Use --force to recreate it."
	return
    fi
    cp $DEVIMAGE_DIR/raspios-lite.img $DEVIMAGE_DIR/$DEVIMAGE_NAME
    modify_image
    cat << EOSUCCESS
XmrSigner Development image created successfully!

Now you can flash you image to a sd card with:
    sudo dd if=${DEVIMAGE_DIR}/${DEVIMAGE_NAME} of=<sdcard device> bs=16M conv=fsync && sudo sync
EOSUCCESS

}

flash() {
    local image_path="$1"

    while true
    do
	echo -n "Scan for devices..."
	# List available removable devices
	devices=$(lsblk -o RM,SIZE,TYPE,NAME,MODEL | grep -v -E '(lvm|part|loop)' | grep -v -E '\s0B\s' | grep -E '^\s?1' || true)
	if [[ -z ${devices} ]]; then
	    echo -e "failed\nNo removable devices found."
	    read -n1 -rp "Would you like to (r)escan, or (q)uit? " choice
	    echo
	    [[ $choice == [qQ] ]] && echo -e "\nOperation cancelled." && return 0
	    [[ $choice == [rR] ]] && echo "" && continue
	    echo -n "\nInvalid choice. Operation cancelled." && return 1
	fi
	echo "done"

	# Parse the device list and store in array
	device_list=()
	while read -r line; do
	    rm=$(echo $line | awk '{print $1}')
	    size=$(echo $line | awk '{print $2}')
	    type=$(echo $line | awk '{print $3}')
	    name=$(echo $line | awk '{print $4}')
	    model=$(echo $line | awk '{print $5, $6, $7, $8}')
	    device_list+=("$name $model ($size)")
	done <<< "$devices"

	echo -e "\nAvailable devices:"
	for i in "${!device_list[@]}"; do
	    echo -e "$((i+1)). ${device_list[$i]}"
	    if [ "$i" -gt 9 ]; then
		    break
	    fi
	done
	read -n 1 -r -p "Select a device to flash the image (enter the number), (r)escan or (q)uit: " selection
	[[ $selection == [qQ] ]] && echo -e "\nOperation cancelled." && return 0
	[[ $selection == [rR] ]] && echo "" && continue

	if [[ "$selection" -lt 1 || "$selection" -gt "${#device_list[@]}" ]]; then
	    echo -e "\nInvalid selection"
	    return
	fi
	selected_device=$(echo "${device_list[$((selection-1))]}" | awk '{print $1}')
	device_path="/dev/$selected_device"
	echo -e "\nSelected device: $device_path"

	# Ask for confirmation
	read -n 3 -r -p "Are you sure you want to destroy all data on $device_path? (yes/no): " confirmation

	if [[ "$confirmation" != "yes" ]]; then
	    echo -e "\nOperation cancelled."
	    return
	fi
	echo -e "\nFlashing image to $device_path..."
	# Flash the image to the selected device
	sudo dd if="$image_path" of="$device_path" bs=16M status=progress conv=fsync && sudo sync
	echo -e "\nImage successfully flashed to $device_path."
    done
}

askdoflash() {
    read -n 1 -p 'Do you want to flash the image to a medium? (y/n): ' doflash
    echo ''
    if [ "$doflash" = "y" ] || [ "$doflash" = "Y" ]; then
	return 0
    fi
    return 1
}

download_pios_image
get_monero_wallet_rpc
check_sudo "$@"
create_image "$1"
if askdoflash; then
    flash "${DEVIMAGE_DIR}/${DEVIMAGE_NAME}"
fi
