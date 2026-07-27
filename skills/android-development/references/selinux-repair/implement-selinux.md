# Implement SELinux

Source: https://source.android.com/docs/security/features/selinux/implement

Converted from the downloaded AOSP HTML snapshot bundled with this skill.

SELinux is set up to default-deny, which means that every single access for which it has a hook in the kernel must be explicitly allowed by policy. This means a policy file is comprised of a large amount of information regarding rules, types, classes, permissions, and more. A full consideration of SELinux is out of the scope of this document, but an understanding of how to write policy rules is now essential when bringing up new Android devices. There is a great deal of information available regarding SELinux already. See Supporting documentation for suggested resources.
## Key files
To enable SELinux, integrate the latest Android kernel and then incorporate the files found in the system/sepolicy directory. When compiled, those files comprise the SELinux kernel security policy and cover the upstream Android operating system.
In general, you shouldn't modify the system/sepolicy files directly. Instead, add or edit your own device-specific policy files in the /device/manufacturer/device-name/sepolicy directory. In Android 8.0 and higher, the changes you make to these files should only affect policy in your vendor directory. For more details on separation of public sepolicy in Android 8.0 and higher, see Customizing SEPolicy in Android 8.0+. Regardless of Android version, you're still modifying these files:
### Policy files
Files that end with *.te are SELinux policy source files, which define domains and their labels. You may need to create new policy files in /device/manufacturer/device-name/sepolicy, but you should try to update existing files where possible.
### Context files
Context files are where you specify labels for your objects.
- file_contexts assigns labels to files and is used by various userspace components. As you create new policies, create or update this file to assign new labels to files. To apply new file_contexts, rebuild the filesystem image or run restorecon on the file to be relabeled. On upgrades, changes to file_contexts are automatically applied to the system and userdata partitions as part of the upgrade. Changes can also be automatically applied on upgrade to other partitions by adding restorecon_recursive calls to your init.board.rc file after the partition has been mounted read-write.
- genfs_contexts assigns labels to filesystems, such as proc or vfat that don't support extended attributes. This configuration is loaded as part of the kernel policy but changes might not take effect for in-core inodes, requiring a reboot or unmounting and re-mounting the filesystem to fully apply the change. Specific labels may also be assigned to specific mounts, such as vfat using the context=mount option.
- property_contexts assigns labels to Android system properties to control what processes can set them. This configuration is read by the init process during startup.
- service_contexts assigns labels to Android binder services to control what processes can add (register) and find (lookup) a binder reference for the service. This configuration is read by the servicemanager process during startup.
- seapp_contexts assigns labels to app processes and /data/data directories. This configuration is read by the zygote process on each app launch and by installd during startup.
- mac_permissions.xml assigns a seinfo tag to apps based on their signature and optionally their package name. The seinfo tag can then be used as a key in the seapp_contexts file to assign a specific label to all apps with that seinfo tag. This configuration is read by system_server during startup.
- keystore2_key_contexts assigns labels to Keystore 2 namespaces. These namespace are enforced by the keystore2 daemon. Keystore has always provided UID/AID based namespaces. Keystore 2 additionally enforces sepolicy defined namespaces. A detailed description of the format and conventions of this file can be found here.
### BoardConfig.mk makefile
After editing or adding policy and context files, update your /device/manufacturer/device-name/BoardConfig.mk makefile to reference the sepolicy subdirectory and each new policy file. For more information about the BOARD_SEPOLICY variables, see system/sepolicy/README file.
```
BOARD_SEPOLICY_DIRS += \
        <root>/device/manufacturer/device-name/sepolicy
BOARD_SEPOLICY_UNION += \
        genfs_contexts \
        file_contexts \
        sepolicy.te
```
After rebuilding, your device is enabled with SELinux. You can now either customize your SELinux policies to accommodate your own additions to the Android operating system as described in Customization or verify your existing setup as covered in Validation.
When the new policy files and BoardConfig.mk updates are in place, the new policy settings are automatically built into the final kernel policy file. For more information about how sepolicy is built on the device, see Building sepolicy.
## Implementation
To get started with SELinux:
- Enable SELinux in the kernel: CONFIG_SECURITY_SELINUX=y
- Change the kernel_cmdline or bootconfig parameter so that:
```
BOARD_KERNEL_CMDLINE := androidboot.selinux=permissive
```
```
BOARD_BOOTCONFIG := androidboot.selinux=permissive
```
- Boot up the system in permissive and see what denials are encountered on boot: On Ubuntu 14.04 or newer:
```
adb shell su -c dmesg | grep denied | audit2allow -p out/target/product/BOARD/root/sepolicy
```
```
adb pull /sys/fs/selinux/policy
adb logcat -b all | audit2allow -p policy
```
- Evaluate the output for warnings that resemble init: Warning! Service name needs a SELinux domain defined; please fix! See Validation for instructions and tools.
- Identify devices, and other new files that need labeling.
- Use existing or new labels for your objects. Look at the *_contexts files to see how things were previously labeled and use knowledge of the label meanings to assign a new one. Ideally, this is an existing label that fits into policy, but sometimes a new label is needed, and rules for access to that label are needed. Add your labels to the appropriate context files.
- Identify domains/processes that should have their own security domains. You likely need to write a completely new policy for each. All services spawned from init, for instance, should have their own. The following commands help reveal those that remain running (but ALL services need such a treatment):
```
adb shell su -c ps -Z | grep init
```
```
adb shell su -c dmesg | grep 'avc: '
```
- Review init.device.rc to identify any domains that don't have a domain type. Give them a domain early in your development process to avoid adding rules to init or otherwise confusing init accesses with ones that are in their own policy.
- Set up BOARD_CONFIG.mk to use BOARD_SEPOLICY_* variables. See the README in system/sepolicy for details on setting this up.
- Examine the init.device.rc and fstab.device file and make sure every use of mount corresponds to a properly labeled filesystem or that a context= mount option is specified.
- Go through each denial and create SELinux policy to properly handle each. See the examples in Customization.
You should start with the policies in the AOSP and then build upon them for your own customizations. For more information about policy strategy and a closer look at some of these steps, see Writing SELinux Policy.
## Use cases
Here are specific examples of exploits to consider when crafting your own software and associated SELinux policies:
Symlinks: Because symlinks appear as files, they are often read as files, which can lead to exploits. For instance, some privileged components, such as init, change the permissions of certain files, sometimes to be excessively open.
Attackers might then replace those files with symlinks to code they control, allowing the attacker to overwrite arbitrary files. But if you know your app never traverses a symlink, you can prohibit it from doing so with SELinux.
System files: Consider the class of system files that should be modified only by the system server. Still, since netd, init, and vold run as root, they can access those system files. So if netd became compromised, it could compromise those files and potentially the system server itself.
With SELinux, you can identify those files as system server data files. Therefore, the only domain that has read/write access to them is system server. Even if netd became compromised, it couldn't switch domains to the system server domain and access those system files although it runs as root.
App data: Another example is the class of functions that must run as root but shouldn't get to access app data. This is incredibly useful as wide-ranging assertions can be made, such as certain domains unrelated to app data being prohibited from accessing the internet.
setattr: For commands such as chmod and chown, you could identify the set of files where the associated domain can conduct setattr. Anything outside of that could be prohibited from these changes, even by root. So an app might run chmod and chown against those labeled app_data_files but not shell_data_files or system_data_files.
