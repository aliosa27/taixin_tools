include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-taixintools
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

PKG_LICENSE:=MIT
PKG_MAINTAINER:=aliosa27@aliosa27.me

LUCI_TITLE:=LuCI Support for TaixinTools
LUCI_DEPENDS:=+python3 +python3-scapy
LUCI_DESCRIPTION:=Web interface for TaixinTools NetAT commands and NetLog viewer

include $(TOPDIR)/feeds/luci/luci.mk

define Package/$(PKG_NAME)/conffiles
/etc/config/taixintools
endef

define Package/$(PKG_NAME)/postinst
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] || {
	# Copy libnetat.py to the system location
	if [ -f /usr/lib/taixintools/libnetat.py ]; then
		chmod +x /usr/lib/taixintools/libnetat.py
	fi
	# Ensure backend scripts are executable
	chmod +x /usr/lib/taixintools/*.sh 2>/dev/null || true
	# Reload uhttpd/rpcd if running
	/etc/init.d/uhttpd reload 2>/dev/null || true
	/etc/init.d/rpcd reload 2>/dev/null || true
	exit 0
}
endef

define Package/$(PKG_NAME)/install
	$(call Package/$(PKG_NAME)/install/Default,$(1))

	# Install libnetat.py to system location
	$(INSTALL_DIR) $(1)/usr/lib/taixintools
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/../../libnetat.py $(1)/usr/lib/taixintools/libnetat.py

	# Install .version file
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/../../.version $(1)/usr/lib/taixintools/.version
endef

# call BuildPackage - OpenWrt buildroot signature
