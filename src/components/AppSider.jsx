// src/components/AppSider.jsx

import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';

const { Sider } = Layout;

/**
 * A recursive function to build the Ant Design Menu items from our config.
 * It handles infinite nesting.
 * @param {Array} items - The array of menu items (from appConfig).
 * @returns {Array} - An array of JSX elements for the <Menu> component.
 */
const renderMenuItems = (items) => {
  return items.map((item) => {
    // If it's a group with children, create a SubMenu and recurse
    if (item.type === 'group' && item.children) {
      return (
        <Menu.SubMenu key={item.key} icon={item.icon} title={item.label}>
          {renderMenuItems(item.children)}
        </Menu.SubMenu>
      );
    }

    // Otherwise, create a standard, clickable Menu.Item
    return (
      <Menu.Item key={item.key} icon={item.icon}>
        <Link to={item.path}>{item.label}</Link>
      </Menu.Item>
    );
  });
};

const AppSider = ({ collapsed, menuItems }) => {
  const location = useLocation();

  /**
   * Recursively finds the keys of all parent groups for the current path.
   * This is essential for keeping the correct submenus open on page load.
   * @param {Array} items - The menu configuration array.
   * @param {string} path - The current URL path.
   * @returns {Array} - An array of keys, e.g., ['management', 'settings-group'].
   */
  const getOpenKeys = (items, path) => {
    for (const item of items) {
      if (item.type === 'group' && item.children) {
        // Check if a direct child's path matches the current path.
        if (item.children.some(child => child.path === path)) {
          return [item.key];
        }
        // If not, search deeper within the children of this group.
        const subPathKeys = getOpenKeys(item.children, path);
        if (subPathKeys.length > 0) {
          // If a match was found in a descendant, return this group's key
          // plus all the keys of the path down to the match.
          return [item.key, ...subPathKeys];
        }
      }
    }
    return []; // Return an empty array if no match is found in this branch.
  };

  return (
    <Sider trigger={null} collapsible collapsed={collapsed}>
      <div className="logo" style={{ height: 64, background: 'rgba(255, 255, 255, 0.2)', margin: 16 }} />
      <Menu
        theme="dark"
        mode="inline"
        // Automatically highlight the item whose key matches the URL
        selectedKeys={[location.pathname]}
        // Automatically open the parent submenus on page load
        defaultOpenKeys={getOpenKeys(menuItems, location.pathname)}
      >
        {renderMenuItems(menuItems)}
      </Menu>
    </Sider>
  );
};

export default AppSider;