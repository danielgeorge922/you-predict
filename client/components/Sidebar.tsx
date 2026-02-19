import React from "react";

const Sidebar = () => {
  return (
    <div className="">
      <nav>
        <ul>
          <li><a href="/dashboard">Dashboard</a></li>
          <li><a href="/analytics">Analytics</a></li>
          <li><a href="/reports">Reports</a></li>
          <li><a href="/users">Users</a></li>
          <li><a href="/settings">Settings</a></li>
          <li><a href="/notifications">Notifications</a></li>
          <li><a href="/help">Help</a></li>
          <li><a href="/profile">Profile</a></li>
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;
