
# Policy compatibility

Source: https://source.android.com/docs/security/features/selinux/compatibility

Converted from the downloaded AOSP HTML snapshot bundled with this skill.

This page describes how Android handles the policy compatibility issues with platform over-the-air (OTA) updates, where new platform SELinux settings might differ from old vendor SELinux settings.

## Object ownership and labeling

Ownership must be clearly defined for each object to keep platform and vendor policy separate. For example, if the vendor policy labels /dev/foo and the platform policy labels /dev/foo in a subsequent OTA, there is undefined behavior like an unexpected denial, or more critically, a boot failure. For SELinux, this manifests as a labeling collision. The device node can have only a single label that resolves to whichever label is applied last. As a result:
- Processes that need access to the unsuccessfully applied label loses access to the resource.
- Processes that gain access to the file might break because the wrong device node was created.
Collisions between platform and vendor labels can occur for any object that has an SELinux label, including properties, services, processes, files, and sockets. To avoid these issues, clearly define ownership of these objects.

### Type/attribute namespacing

In addition to label collisions, SELinux type and attribute names can also collide. SELinux doesn't allow multiple declarations of the same types and attributes. A policy with duplicate declarations fails to compile. To avoid type and attribute name collisions, all vendor declarations are highly recommended to start with the vendor_ prefix. For example, vendors should use type vendor_foo, domain; instead of type foo, domain;.

### File ownership

Preventing collisions for files is challenging because platform and vendor policy both commonly provide labels for all filesystems. Unlike type naming, namespacing of files isn't practical since many of them are created by the kernel. To prevent these collisions, follow the naming guidance for filesystems in this section. For Android 8.0, these are recommendations without technical enforcement. In the future, these recommendations will be enforced by the Vendor Test Suite (VTS).

#### System (/system)

Only the system image must provide labels for /system components through file_contexts, service_contexts, etc. If labels for /system components are added in the vendor policy, a framework-only OTA update might not be possible.

#### Vendor (/vendor)

The AOSP SELinux policy already labels parts of the vendor partition the platform interacts with, which enables writing SELinux rules for platform processes to be able to talk or access parts of the vendor partition. Examples: As a result, specific rules must be followed (enforced through neverallows) when labelling additional files in the vendor partition:
- vendor_file must be the default label for all files in the vendor partition. The platform policy requires this to access passthrough HAL implementations.
- All new exec_types added in the vendor partition through the vendor policy must have vendor_file_type attribute. This is enforced through neverallows.
- To avoid conflicts with future platform/framework updates, avoid labelling files other than exec_types in the vendor partition.
- All library dependencies for AOSP-identified same process HALs must be labelled as same_process_hal_file.

#### Procfs (/proc)

Files in /proc may be labeled using only the genfscon label. In Android 7.0, both the platform and vendor policy used genfscon to label files in procfs. Recommendation: Only platform policy labels /proc. If vendor processes need access to files in /proc that are currently labeled with the default label (proc), the vendor policy shouldn't explicitly label them and should instead use the generic proc type to add rules for vendor domains. This allows the platform updates to accommodate future kernel interfaces exposed through procfs and label them explicitly as needed.

#### Debugfs (/sys/kernel/debug)

Debugfs can be labeled in both file_contexts and genfscon. In Android 7.0 to Android 10, both platform and vendor label debugfs. In Android 11, debugfs can't be accessed or mounted on production devices. Device manufacturers should remove debugfs.

#### Tracefs (/sys/kernel/debug/tracing)

Tracefs can be labeled in both file_contexts and genfscon. In Android 7.0, only the platform labels tracefs. Recommendation: Only platform may label tracefs.

#### Sysfs (/sys)

Files in /sys may be labeled using both file_contexts and genfscon. In Android 7.0, both the platform and the vendor use genfscon to label files in sysfs. Recommendation: The platform may label sysfs nodes that aren't device-specific. Otherwise, only vendor may label files.

#### tmpfs (/dev)

Files in /dev may be labeled in file_contexts. In Android 7.0, both the platform and the vendor label files here. Recommendation: Vendor may label only files in /dev/vendor (for example, /dev/vendor/foo, /dev/vendor/socket/bar).

#### Rootfs (/)

Files in / may be labeled in file_contexts. In Android 7.0, both platform and vendor label files here. Recommendation: Only system may label files in /.

#### Data (/data)

Data is labeled through a combination of file_contexts and seapp_contexts. Recommendation: Disallow vendor labeling outside /data/vendor. Only platform may label other parts of /data.

#### Genfs labels version

Starting with vendor API level 202504, newer SELinux labels assigned with genfscon in system/sepolicy/compat/plat_sepolicy_genfs_ver.cil are optional for older vendor partitions. This allows older vendor partitions to keep their existing SEPolicy implementation. This is controlled by the Makefile variable BOARD_GENFS_LABELS_VERSION which is stored in /vendor/etc/selinux/genfs_labels_version.txt. Example:
- In vendor API level 202404, the /sys/class/udc node is labeled sysfs by default.
- Starting from vendor API level 202504, /sys/class/udc is labeled sysfs_udc.
However, /sys/class/udc might be in use by vendor partitions using API level 202404, either with the default sysfs label or a vendor-specific label. Unconditionally labeling /sys/class/udc as sysfs_udc could break compatibility with these vendor partitions. By checking BOARD_GENFS_LABELS_VERSION, the platform keeps using the previous labels and permissions for the older vendor partitions. BOARD_GENFS_LABELS_VERSION can be greater than or equal to vendor API level. For instance, vendor partitions using API level 202404 can set BOARD_GENFS_LABELS_VERSION to 202504 to adopt new labels introduced in 202504. See the list of 202504-specific genfs labels. When labeling genfscon nodes, the platform must consider older vendor partitions and implement fallback mechanisms for compatibility when needed. The platform can use platform-only libraries to query the genfs labels version.
- On native, use libgenfslabelsversion. See genfslabelsversion.h for the header file of libgenfslabelsversion.
- On Java, use android.os.SELinux.getGenfsLabelsVersion().

## Platform-public policy

The platform SELinux policy is divided into private and public. The platform-public policy consists of types and attributes that are always available for a vendor API level, acting as an API between platform and vendor. This policy is exposed to vendor policy writers to enable vendors to build vendor policy files, which when combined with the platform-private policy, results in a fully functional policy for a device. The platform-public policy is defined in system/sepolicy/public. For example, a type vendor_init, representing the init process in the context of vendor, is defined under system/sepolicy/public/vendor_init.te:
```
type vendor_init, domain;
```

Vendors can refer to the type vendor_init to write custom policy rules:
```
# Allow vendor_init to set vendor_audio_prop in vendor's init scripts
set_prop(vendor_init, vendor_audio_prop)
```

### Compatibility attributes

SELinux policy is an interaction between source and target types for specific object classes and permissions. Every object (for example, processes, files) affected by SELinux policy can have only one type, but that type might have multiple attributes. The policy is written mostly in terms of existing types. Here, both vendor_init and debugfs are types:
```
allow vendor_init debugfs:dir { mounton };
```

This works because the policy was written with knowledge of all types. However, if the vendor policy and platform policy use specific types, and the label of a specific object changes in only one of those policies, the other might contain policy that gained or lost access previously relied upon. For example, suppose that the platform policy labels sysfs nodes as sysfs:
```
/sys(/.*)? u:object_r:sysfs:s0
```

The vendor policy grants access to /sys/usb, labeled as sysfs:
```
allow vendor_init sysfs:chr_file rw_file_perms;
```

If the platform policy is changed to label /sys/usb as sysfs_usb, the vendor policy remains the same, but vendor_init loses access to /sys/usb due to the lack of policy for the new sysfs_usb type:
```
/sys/usb u:object_r:sysfs_usb:s0
```

To solve this issue, Android introduces a concept of versioned attributes. At compile time, the build system automatically translates platform public types used in the vendor policy into these versioned attributes. This translation is enabled by mapping files that associate a versioned attribute with one or more public types from the platform. For example, suppose that /sys/usb is labeled as sysfs in 202504 platform policy, and 202504 vendor policy grants vendor_init access to /sys/usb. In this case:
- The vendor policy writes a rule allow vendor_init sysfs:chr_file rw_file_perms;, because /sys/usb is labeled as sysfs in 202504 platform policy. When the build system compiles vendor policy, it automatically translates the rule into allow vendor_init_202504 sysfs_202504:chr_file rw_file_perms;. The attributes vendor_init_202504 and sysfs_202504 correspond to the types vendor_init and sysfs, which are the types defined by the platform.
- The build system generates an identity mapping file /system/etc/selinux/mapping/202504.cil. As both the system and vendor partitions use the same 202504 version, the mapping file contains identity mappings from type_202504 to type. For example, vendor_init_202504 is mapped to vendor_init, and sysfs_202504 is mapped to sysfs:
```
(typeattributeset sysfs_202504 (sysfs))
(typeattributeset vendor_init_202504 (vendor_init))
...
```

When the version is bumped from 202504 to 202604, a new mapping file for 202504 vendor partitions is created under system/sepolicy/private/compat/202504/202504.cil, which is installed to /system/etc/selinux/mapping/202504.cil for the 202604 or newer system partitions. Initially, this mapping file contains identity mappings, as previously described. If a new label sysfs_usb for /sys/usb is added to the 202604 platform policy, the mapping file is updated to map sysfs_202504 to sysfs_usb:
```
(typeattributeset sysfs_202504 (sysfs sysfs_usb))
(typeattributeset vendor_init_202504 (vendor_init))
...
```

This update allows the converted vendor policy rule allow vendor_init_202504 sysfs_202504:chr_file rw_file_perms; to automatically grant vendor_init access to the new sysfs_usb type. To maintain compatibility with older vendor partitions, whenever a new public type is added, that type must be mapped to at least one of versioned attributes in the mapping file system/sepolicy/private/compat/ver/ver.cil, or be listed under system/sepolicy/private/compat/ver/ver.ignore.cil to state that there is no matching type in the previous vendor versions. The combination of the platform policy, the vendor policy, and the mapping file allows the system to update without updating the vendor policy. Also the conversion into the versioned attributes happens automatically, so the vendor policy doesn't need to take care of the versioning, keeping using the public types as is.

### system_ext public and product public policy

Starting in Android 11, the system_ext and the product partitions are allowed to export their designated public types to the vendor partition. Like the platform public policy, the vendor policy uses types and rules automatically translated into the versioned attributes, for example, from type into type_ver, where ver is the vendor API level of the vendor partition. When the system_ext and the product partitions are based on the same platform version ver, the build system generates base mapping files to system_ext/etc/selinux/mapping/ver.cil and product/etc/selinux/mapping/ver.cil, which contain identity mappings from type to type_ver. The vendor policy can access type with the versioned attribute type_ver. In case that only the system_ext and the product partitions are updated, say ver to ver+1 (or later), while the vendor partition stays at ver, the vendor policy might lose access to the types of the system_ext and the product partitions. To prevent breakage, the system_ext and the product partitions should provide mapping files from concrete types into type_ver attributes. Each partner is responsible for maintaining the mapping files, if they support ver vendor partition with ver+1 (or later) system_ext and product partitions. To install mapping files to the system_ext and the product partitions, device implementers, or vendors are expected to:
- Copy the generated base mapping files from ver system_ext and product partitions to their source tree.
- Amend the mapping files as needed.
- Install the mapping files to ver+1 (or later) system_ext and product partitions.
For example, suppose that the 202504 system_ext partition has one public type named foo_type. Then system_ext/etc/selinux/mapping/202504.cil in the 202504 system_ext partition looks like this:
```
(typeattributeset foo_type_202504 (foo_type))
(expandtypeattribute foo_type_202504 true)
(typeattribute foo_type_202504)
```

If bar_type is added to the 202604 system_ext, and if bar_type should be mapped to foo_type for the 202504 vendor partition, 202504.cil can be updated from (typeattributeset foo_type_202504 (foo_type)) to (typeattributeset foo_type_202504 (foo_type bar_type)) and then installed to the 202604 system_ext partition. The 202504 vendor partition can continue accessing to the 202604 system_ext's foo_type and bar_type.

## Attribute changes for Android 9

Devices upgrading to Android 9 can use the following attributes, but devices launching with Android 9 must not.

### Violator attributes

Android 9 includes these domain-related attributes:
- data_between_core_and_vendor_violators. Attribute for all domains that violate the requirement of not sharing files by path between vendor and coredomains. Platform and vendor processes shouldn't use on-disk files to communicate (unstable ABI). Recommendation:
- Vendor code should use /data/vendor.
- System shouldn't use /data/vendor.
- system_executes_vendor_violators. Attribute for all system domains (except init and shell domains) that violate the requirement of not executing vendor binaries. Execution of vendor binaries has unstable API. Platform shouldn't execute vendor binaries directly. Recommendation:
- Such platform dependencies on vendor binaries must be behind HIDL HALs.
OR
- coredomains that need access to vendor binaries should be moved to the vendor partition and thus, stop being coredomain.

### Untrusted attributes

Untrusted apps that host arbitrary code shouldn't have access to HwBinder services, except those considered sufficiently safe for access from such apps (see safe services below). The two main reasons for this are:
- HwBinder servers don't perform client authentication because HIDL currently doesn't expose caller UID information. Even if HIDL did expose such data, many HwBinder services either operate at a level below that of apps (such as, HALs) or must not rely on app identity for authorization. Thus, to be safe, the default assumption is that every HwBinder service treats all its clients as equally authorized to perform operations offered by the service.
- HAL servers (a subset of HwBinder services) contain code with higher incidence rate of security issues than system/core components and have access to the lower layers of the stack (all the way down to hardware) thus increasing opportunities for bypassing the Android security model.

#### Safe services

Safe services include:
- same_process_hwservice. These services (by definition) run in the process of the client and thus have the same access as the client domain in which the process runs.
- coredomain_hwservice. These services don't pose risks associated with reason #2.
- hal_configstore_ISurfaceFlingerConfigs. This service is specifically designed for use by any domain.
- hal_graphics_allocator_hwservice. These operations are also offered by surfaceflinger Binder service, which apps are permitted to access.
- hal_omx_hwservice. This is a HwBinder version of the mediacodec Binder service, which apps are permitted to access.
- hal_codec2_hwservice. This is a newer version of hal_omx_hwservice.

#### Useable attributes

All hwservices not considered safe have the attribute untrusted_app_visible_hwservice. The corresponding HAL servers have the attribute untrusted_app_visible_halserver. Devices launching with Android 9 MUST NOT use either untrusted attribute. Recommendation:
- Untrusted apps should instead talk to a system service that talks to the vendor HIDL HAL. For example, apps can talk to binderservicedomain, then mediaserver (which is a binderservicedomain) in turn talks to the hal_graphics_allocator.
OR
- Apps that need direct access to vendor HALs should have their own vendor-defined sepolicy domain.

### File attribute tests

Android 9 includes build time tests that ensure all files in specific locations have the appropriate attributes (such as, all files in sysfs have the required sysfs_type attribute).

## SELinux contexts labeling

To support the distinction between platform and vendor sepolicy, the system builds SELinux context files differently to keep them separate.

### File contexts

Android 8.0 introduced the following changes for file_contexts:
- To avoid additional compilation overhead on device during boot, file_contexts cease to exist in the binary form. Instead, they are readable, regular expression text file such as {property, service}_contexts (as they were pre-7.0).
- The file_contexts are split between two files:
- plat_file_contexts
- Android platform file_context that has no device-specific labels, except for labeling parts of /vendor partition that must be labeled precisely to ensure proper functioning of the sepolicy files.
- Must reside in system partition at /system/etc/selinux/plat_file_contexts on device and be loaded by init at the start along with the vendor file_context.
- vendor_file_contexts
- Device-specific file_context built by combining file_contexts found in the directories pointed to by BOARD_SEPOLICY_DIRS in the device's Boardconfig.mk files.
- Must be installed at /vendor/etc/selinux/vendor_file_contexts in vendor partition and be loaded by init at the start along with the platform file_context.

### Property contexts

In Android 8.0, the property_contexts is split between two files:
- plat_property_contexts
- Android platform property_context that has no device-specific labels.
- Must reside in system partition at /system/etc/selinux/plat_property_contexts and be loaded by init at the start along with the vendor property_contexts.
- vendor_property_contexts
- Device-specific property_context built by combining property_contexts found in the directories pointed to by BOARD_SEPOLICY_DIRS in device's Boardconfig.mk files.
- Must reside in vendor partition at /vendor/etc/selinux/vendor_property_contexts and be loaded by init at the start along with the platform property_context

### Service contexts

In Android 8.0, the service_contexts is split between the following files:
- plat_service_contexts
- Android platform-specific service_context for the servicemanager. The service_context has no device-specific labels.
- Must reside in system partition at /system/etc/selinux/plat_service_contexts and be loaded by servicemanager at the start along with the vendor service_contexts.
- vendor_service_contexts
- Device-specific service_context built by combining service_contexts found in the directories pointed to by BOARD_SEPOLICY_DIRS in the device's Boardconfig.mk files.
- Must reside in vendor partition at /vendor/etc/selinux/vendor_service_contexts and be loaded by servicemanager at the start along with the platform service_contexts.
- Although servicemanager looks for this file at boot time, for a fully compliant TREBLE device, the vendor_service_contexts MUST NOT exist. This is because all interaction between vendor and system processes MUST go through hwservicemanager/hwbinder.
- plat_hwservice_contexts
- Android platform hwservice_context for hwservicemanager that has no device-specific labels.
- Must reside in system partition at /system/etc/selinux/plat_hwservice_contexts and be loaded by hwservicemanager at the start along with the vendor_hwservice_contexts.
- vendor_hwservice_contexts
- Device-specific hwservice_context built by combining hwservice_contexts found in the directories pointed to by BOARD_SEPOLICY_DIRS in the device's Boardconfig.mk files.
- Must reside in vendor partition at /vendor/etc/selinux/vendor_hwservice_contexts and be loaded by hwservicemanager at the start along with the plat_service_contexts.
- vndservice_contexts
- Device-specific service_context for the vndservicemanager built by combining vndservice_contexts found in the directories pointed to by BOARD_SEPOLICY_DIRS in the device's Boardconfig.mk.
- This file must reside in vendor partition at /vendor/etc/selinux/vndservice_contexts and be loaded by vndservicemanager at the start.

### Seapp contexts

In Android 8.0, the seapp_contexts is split between two files:
- plat_seapp_contexts
- Android platform seapp_context that has no device-specific changes.
- Must reside in system partition at /system/etc/selinux/plat_seapp_contexts.
- vendor_seapp_contexts
- Device-specific extension to platform seapp_context built by combining seapp_contexts found in the directories pointed to by BOARD_SEPOLICY_DIRS in the device's Boardconfig.mk files.
- Must reside in vendor partition at /vendor/etc/selinux/vendor_seapp_contexts.

### MAC permissions

In Android 8.0, the mac_permissions.xml is split between two files:
- Platform mac_permissions.xml
- Android platform mac_permissions.xml that has no device-specific changes.
- Must reside in system partition at /system/etc/selinux/.
- Non-Platform mac_permissions.xml
- Device-specific extension to platform mac_permissions.xml built from mac_permissions.xml found in the directories pointed to by BOARD_SEPOLICY_DIRS in the device's Boardconfig.mk files.
- Must reside in vendor partition at /vendor/etc/selinux/.
