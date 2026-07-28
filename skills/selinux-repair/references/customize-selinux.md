
# Customize SELinux

Source: https://source.android.com/docs/security/features/selinux/customize

Converted from the downloaded AOSP HTML snapshot bundled with this skill.

After you've integrated the base level of SELinux functionality and thoroughly analyzed the results, you may add your own policy settings to cover your customizations to the Android operating system. These policies must still meet the Android Compatibility program requirements and must not remove the default SELinux settings. Manufacturers shouldn't remove existing SELinux policy. Otherwise, they risk breaking the Android SELinux implementation and the apps it governs. This includes third-party apps that will likely need to be improved to be compliant and operational. Apps must require no modification to continue functioning on SELinux-enabled devices. When embarking upon customizing SELinux, remember to:
- Write SELinux policy for all new daemons
- Use predefined domains whenever appropriate
- Assign a domain to any process spawned as an init service
- Become familiar with the macros before writing policy
- Submit changes to core policy to AOSP
And remember not to:
- Create incompatible policy
- Allow end user policy customization
- Allow MDM policy customizations
- Scare users with policy violations
- Add backdoors
See the Kernel Security Features section of the Android Compatibility Definition document for specific requirements. SELinux uses a whitelist approach, meaning all access must be explicitly allowed in policy in order to be granted. Since Android's default SELinux policy already supports the Android Open Source Project, you aren't required to modify SELinux settings in any way. If you do customize SELinux settings, take great care not to break existing apps. To get started:
- Use the latest Android kernel.
- Adopt the principle of least privilege.
- Address only your own additions to Android. The default policy works with the Android Open Source Project codebase automatically.
- Compartmentalize software components into modules that conduct singular tasks.
- Create SELinux policies that isolate those tasks from unrelated functions.
- Put those policies in *.te files (the extension for SELinux policy source files) within the /device/manufacturer/device-name/sepolicy directory and use BOARD_SEPOLICY variables to include them in your build.
- Make new domains permissive initially. This is done by using a permissive declaration in the domain's .te file.
- Analyze results and refine your domain definitions.
- Remove the permissive declaration when no further denials appear in userdebug builds.
After you've integrated your SELinux policy change, add a step to your development workflow to ensure SELinux compatibility going forward. In an ideal software development process, SELinux policy changes only when the software model changes and not the actual implementation. As you start customizing SELinux, first audit your additions to Android. If you've added a component that conducts a new function, ensure the component meets Android's security policy, as well as any associated policy crafted by the OEM, before turning on enforcing mode. To prevent unnecessary issues, it is better to be overbroad and over-compatible than too restrictive and incompatible, which results in broken device functions. Conversely, if your changes will benefit others, you should submit the modifications to the default SELinux policy as a patch. If the patch is applied to the default security policy, you won't need to make this change with each new Android release.

## Example policy statements

SELinux is based upon the M4 computer language and therefore supports a variety of macros to save time. In the following example, all domains are granted access to read from or write to /dev/null and read from /dev/zero.
```
# Allow read / write access to /dev/null
allow domain null_device:chr_file { getattr open read ioctl lock append write};
# Allow read-only access to /dev/zero
allow domain zero_device:chr_file { getattr open read ioctl lock };
```

This same statement can be written with SELinux *_file_perms macros (shorthand):
```
# Allow read / write access to /dev/null
allow domain null_device:chr_file rw_file_perms;
# Allow read-only access to /dev/zero
allow domain zero_device:chr_file r_file_perms;
```

## Example policy

Here is a complete example policy for DHCP, which we examine below:
```
type dhcp, domain;
permissive dhcp;
type dhcp_exec, exec_type, file_type;
type dhcp_data_file, file_type, data_file_type;
init_daemon_domain(dhcp)
net_domain(dhcp)
allow dhcp self:capability { setgid setuid net_admin net_raw net_bind_service
};
allow dhcp self:packet_socket create_socket_perms;
allow dhcp self:netlink_route_socket { create_socket_perms nlmsg_write };
allow dhcp shell_exec:file rx_file_perms;
allow dhcp system_file:file rx_file_perms;
# For /proc/sys/net/ipv4/conf/*/promote_secondaries
allow dhcp proc_net:file write;
allow dhcp system_prop:property_service set ;
unix_socket_connect(dhcp, property, init)
type_transition dhcp system_data_file:{ dir file } dhcp_data_file;
allow dhcp dhcp_data_file:dir create_dir_perms;
allow dhcp dhcp_data_file:file create_file_perms;
allow dhcp netd:fd use;
allow dhcp netd:fifo_file rw_file_perms;
allow dhcp netd:{ dgram_socket_class_set unix_stream_socket } { read write };
allow dhcp netd:{ netlink_kobject_uevent_socket netlink_route_socket
netlink_nflog_socket } { read write };
```

Let’s dissect the example: In the first line, the type declaration, the DHCP daemon inherits from the base security policy (domain). From the previous statement examples, DHCP can read from and write to /dev/null. In the second line, DHCP is identified as a permissive domain. In the init_daemon_domain(dhcp) line, the policy states DHCP is spawned from init and is allowed to communicate with it. In the net_domain(dhcp) line, the policy allows DHCP to use common network functionality from the net domain such as reading and writing TCP packets, communicating over sockets, and conducting DNS requests. In the line allow dhcp proc_net:file write;, the policy states DHCP can write to specific files in /proc. This line demonstrates SELinux's fine-grained file labeling. It uses the proc_net label to limit write access to only the files under /proc/sys/net. The final block of the example starting with allow dhcp netd:fd use; depicts how apps may be allowed to interact with one another. The policy says DHCP and netd may communicate with one another via file descriptors, FIFO files, datagram sockets, and UNIX stream sockets. DHCP may only read to and write from the datagram sockets and UNIX stream sockets and not create or open them.

## Available controls

```
ioctl read write create getattr setattr lock relabelfrom relabelto append
unlink link rename execute swapon quotaon mounton
```

```
add_name remove_name reparent search rmdir open audit_access execmod
```

```
ioctl read write create getattr setattr lock relabelfrom relabelto append bind
connect listen accept getopt setopt shutdown recvfrom sendto recv_msg send_msg
name_bind
```

```
mount remount unmount getattr relabelfrom relabelto transition associate
quotamod quotaget
```

```
fork transition sigchld sigkill sigstop signull signal ptrace getsched setsched
getsession getpgid setpgid getcap setcap share getattr setexec setfscreate
noatsecure siginh setrlimit rlimitinh dyntransition setcurrent execmem
execstack execheap setkeycreate setsockcreate
```

```
compute_av compute_create compute_member check_context load_policy
compute_relabel compute_user setenforce setbool setsecparam setcheckreqprot
read_policy
```

```
chown dac_override dac_read_search fowner fsetid kill setgid setuid setpcap
linux_immutable net_bind_service net_broadcast net_admin net_raw ipc_lock
ipc_owner sys_module sys_rawio sys_chroot sys_ptrace sys_pacct sys_admin
sys_boot sys_nice sys_resource sys_time sys_tty_config mknod lease audit_write
audit_control setfcap
```

MORE AND MORE

## neverallow rules

SELinux neverallow rules prohibit behavior that should never occur. With compatibility testing, SELinux neverallow rules are now enforced across devices. The following guidelines are intended to help manufacturers avoid errors related to neverallow rules during customization. The rule numbers used here correspond to Android 5.1 and are subject to change by release. Rule 48: neverallow { domain -debuggerd -vold -dumpstate -system_server } self:capability sys_ptrace; See the man page for ptrace. The sys_ptrace capability grants the ability to ptrace any process, which allows a great deal of control over other processes and should belong only to designated system components, outlined in the rule. The need for this capability often indicates the presence of something that isn't meant for user-facing builds or functionality that isn't needed. Remove the unnecessary component. Rule 76: neverallow { domain -appdomain -dumpstate -shell -system_server -zygote } { file_type -system_file -exec_type }:file execute; This rule is intended to prevent the execution of arbitrary code on the system. Specifically, it asserts that only code on /system gets executed, which allows security guarantees thanks to mechanisms such as Verified Boot. Often, the best solution when encountering a problem with this neverallow rule is to move the offending code to the /system partition.

## Customize SEPolicy in Android 8.0 and higher

This section provides guidelines for vendor SELinux policy in Android 8.0 and higher, including details on Android Open Source Project (AOSP) SEPolicy and SEPolicy extensions. For more information about how SELinux policy is kept compatible across partitions and Android versions, see Compatibility.

### Policy placement

In Android 7.0 and earlier, device manufacturers could add policy to BOARD_SEPOLICY_DIRS, including policy meant to augment AOSP policy across different device types. In Android 8.0 and higher, adding a policy to BOARD_SEPOLICY_DIRS places the policy only in the vendor image. In Android 8.0 and higher, policy exists in the following locations in AOSP:
- system/sepolicy/public. Includes policy exported for use in vendor-specific policy. Everything goes into the Android 8.0 compatibility infrastructure. Public policy is meant to persist across releases so you can include anything /public in your customized policy. Because of this, the type of policy that can be placed in /public is more restricted. Consider this the platform's exported policy API: Anything that deals with the interface between /system and /vendor belongs here.
- system/sepolicy/private. Includes policy necessary for the functioning of the system image, but of which vendor image policy should have no knowledge.
- system/sepolicy/vendor. Includes policy for components that go in /vendor but exist in the core platform tree (not device-specific directories). This is an artifact of build system's distinction between devices and global components; conceptually this is a part of the device-specific policy described below.
- device/manufacturer/device-name/sepolicy. Includes device-specific policy. Also includes device customizations to policy, which in Android 8.0 and higher corresponds to policy for components on the vendor image.
In Android 11 and higher, system_ext and product partitions can also include partition-specific policies. system_ext and product policies are also split into public and private, and vendors can use system_ext's and product's public policies, like the system policy.
- SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS. Includes policy exported for use in vendor-specific policy. Installed to system_ext partition.
- SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS. Includes policy necessary for the functioning of the system_ext image, but of which vendor image policy should have no knowledge. Installed to system_ext partition.
- PRODUCT_PUBLIC_SEPOLICY_DIRS. Includes policy exported for use in vendor-specific policy. Installed to product partition.
- PRODUCT_PRIVATE_SEPOLICY_DIRS. Includes policy necessary for the functioning of the product image, but of which vendor image policy should have no knowledge. Installed to product partition.

### Supported policy scenarios

On devices launching with Android 8.0 and higher, the vendor image must work with the OEM system image and the reference AOSP system image provided by Google (and pass CTS on this reference image). These requirements ensure a clean separation between the framework and the vendor code. Such devices support the following scenarios.

#### vendor-image-only extensions

Example: Adding a new service to vndservicemanager from the vendor image that supports processes from the vendor image. As with devices launching with previous Android versions, add device-specific customization in device/manufacturer/device-name/sepolicy. New policy governing how vendor components interact with (only) other vendor components should involve types present only in device/manufacturer/device-name/sepolicy. Policy written here allows code on vendor to work, won't be updated as part of a framework-only OTA, and is present in the combined policy on a device with the reference AOSP system image.

#### vendor-image support to work with AOSP

Example: Adding a new process (registered with hwservicemanager from the vendor image) that implements an AOSP-defined HAL. As with devices launching with previous Android versions, perform device-specific customization in device/manufacturer/device-name/sepolicy. The policy exported as part of system/sepolicy/public/ is available for use, and is shipped as part of the vendor policy. Types and attributes from the public policy may be used in new rules dictating interactions with the new vendor-specific bits, subject to the provided neverallow restrictions. As with the vendor-only case, new policy here won't be updated as part of a framework-only OTA and is present in the combined policy on a device with the reference AOSP system image.

#### system-image-only extensions

Example: Adding a new service (registered with servicemanager) that is accessed only by other processes from the system image. Add this policy to system/sepolicy/private. You can add extra processes or objects to enable functionality in a partner system image, provided those new bits don't need to interact with new components on the vendor image (specifically, such processes or objects must fully function without policy from the vendor image). The policy exported by system/sepolicy/public is available here just as it is for vendor-image-only extensions. This policy is part of the system image and could be updated in a framework-only OTA, but will not be present when using the reference AOSP system image.

#### vendor-image extensions that serve extended AOSP components

Example: A new, non-AOSP HAL for use by extended clients that also exist in the AOSP system image (such as an extended system_server). Policy for interaction between system and vendor must be included in the device/manufacturer/device-name/sepolicy directory shipped on the vendor partition. This is similar to the above scenario of adding vendor-image support to work with the reference AOSP image, except the modified AOSP components may also require additional policy to properly operate with the rest of the system partition (which is fine as long as they still have the public AOSP type labels). Policy for interaction of public AOSP components with system-image-only extensions should be in system/sepolicy/private.

#### system-image extensions that access only AOSP interfaces

Example: A new, non-AOSP system process must access a HAL on which AOSP relies. This is similar to the system-image-only extension example, except new system components may interact across the system/vendor interface. Policy for the new system component must go in system/sepolicy/private, which is acceptable provided it is through an interface already established by AOSP in system/sepolicy/public (that is, the types and attributes required for functionality are there). While policy could be included in the device-specific policy, it would be unable to use other system/sepolicy/private types or change (in any policy-affecting way) as a result of a framework-only update. The policy may be changed in a framework-only OTA, but won't be present when using an AOSP system image (which won't have the new system component either).

#### vendor-image extensions that serve new system components

Example: Adding a new, non-AOSP HAL for use by a client process without an AOSP analogue (and thus requires its own domain). Similar to the AOSP-extensions example, policy for interactions between system and vendor must go in the device/manufacturer/device-name/sepolicy directory shipped on the vendor partition (to ensure the system policy has no knowledge of vendor-specific details). You can add new public types that extend the policy in system/sepolicy/public; this should be done only in addition to the existing AOSP policy, that is, don't remove AOSP public policy. The new public types can then be used for policy in system/sepolicy/private and in device/manufacturer/device-name/sepolicy. Keep in mind that every addition to system/sepolicy/public adds complexity by exposing a new compatibility guarantee that must be tracked in a mapping file and which is subject to other restrictions. Only new types and corresponding allow rules may be added in system/sepolicy/public; attributes and other policy statements aren't supported. In addition, new public types cannot be used to directly label objects in the /vendor policy.

### Unsupported policy scenarios

Devices launching with Android 8.0 and higher don't support the following policy scenario and examples.

#### Additional extensions to system-image that need permission to new vendor-image components after a framework-only OTA

Example: A new non-AOSP system process, requiring its own domain, is added in the next Android release and needs access to a new, non-AOSP HAL. Similar to new (non-AOSP) system and vendor components interaction, except the new system type is introduced in a framework-only OTA. Although the new type could be added to the policy in system/sepolicy/public, the existing vendor policy has no knowledge of the new type as it is tracking only the Android 8.0 system public policy. AOSP handles this by exposing vendor-provided resources via an attribute (for example, hal_foo attribute) but as attribute partner extensions aren't supported in system/sepolicy/public, this method is unavailable to vendor policy. Access must be provided by a previously-existing public type. Example: A change to a system process (AOSP or non-AOSP) must change how it interacts with new, non-AOSP vendor component. The policy on the system image must be written without knowledge of specific vendor customizations. Policy concerning specific interfaces in AOSP is thus exposed via attributes in system/sepolicy/public so that vendor policy can opt-in to future system policy which uses these attributes. However, attribute extensions in system/sepolicy/public aren't supported, so all policy dictating how the system components interact with new vendor components (and which isn't handled by attributes already present in AOSP system/sepolicy/public) must be in device/manufacturer/device-name/sepolicy. This means that system types cannot change the access allowed to vendor types as part of a framework-only OTA.
