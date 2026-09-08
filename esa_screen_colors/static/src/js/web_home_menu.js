/** @odoo-module **/

import { Component, useState, useRef, useEffect, useExternalListener } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { fuzzyLookup } from "@web/core/utils/search";
import { useBus, useService } from "@web/core/utils/hooks";
import { loadCSS } from "@web/core/assets";

const NBR_ICONS = 6;

export class ESAHomeMenu extends Component {
    static template = "ESAHomeMenu";
    
    setup() {
        this.state = useState({
            searchQuery: "",
            focusIndex: null,
            apps: [],
            menuItems: [],
            isSearching: false,
            isComposing: false, // For handling composition input (e.g., Japanese IME)
        });

        this.menuService = useService("menu");
        this.router = useService("router");

        this.searchInputRef = useRef("searchInput");

        useBus(this.env.bus, "keydown", this.onKeydown);
        useExternalListener(window, "resize", this.onResize);

        useEffect(() => {
            this.initializeMenu();
        }, []);
    }

    async initializeMenu() {
        const menuData = await this.menuService.getMenu();
        this.fullMenuData = this.processMenuData(menuData);
        this.state.apps = this.fullMenuData.filter(menu => menu.is_app);
    }

    processMenuData(menuData) {
        return menuData.children.flatMap(menu => {
            return menu.children.map(subMenu => ({
                label: subMenu.name,
                id: subMenu.id,
                xmlid: subMenu.xmlid,
                action: subMenu.action || "",
                is_app: !subMenu.parent_id,
                web_icon: subMenu.web_icon,
                web_icon_data: subMenu.web_icon_data,
                parents: menu.name,
            }));
        });
    }

    onKeydown(ev) {
        if (document.activeElement !== this.searchInputRef.el) {
            return;
        }
        const { focusIndex, apps, menuItems } = this.state;
        let newIndex = focusIndex ?? -1;

        switch (ev.key) {
            case "ArrowDown":
                newIndex += 1;
                break;
            case "ArrowUp":
                newIndex -= 1;
                break;
            case "Enter":
                if (focusIndex !== null) {
                    this.openMenu(apps.concat(menuItems)[focusIndex]);
                }
                return;
            case "Escape":
                this.state.searchQuery = "";
                this.state.isSearching = false;
                this.state.focusIndex = null;
                return;
        }

        const totalItems = apps.length + menuItems.length;
        this.state.focusIndex = (newIndex + totalItems) % totalItems;
    }

    openMenu(menu) {
        if (menu.action) {
            this.router.navigate({ menu_id: menu.id, action: menu.action });
        } else {
            this.router.navigate({ menu_id: menu.id });
        }
    }

    onSearchInput(ev) {
        const searchQuery = ev.target.value;
        this.state.searchQuery = searchQuery;
        this.state.isSearching = !!searchQuery;

        if (!searchQuery) {
            this.state.menuItems = [];
            return;
        }

        this.state.menuItems = fuzzyLookup(searchQuery, this.fullMenuData, menu => [menu.label, menu.parents]);
        this.state.focusIndex = 0;
    }

    onMenuClick(menu) {
        this.openMenu(menu);
    }

    onResize() {
        this.state.isSearching = false;
    }
}

// Register component in Odoo
registry.category("actions").add("esa_home_menu", ESAHomeMenu);

console.log("===============")
