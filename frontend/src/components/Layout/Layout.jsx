import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const sideW = collapsed ? 64 : 220;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <main style={{ flex: 1, marginLeft: sideW, minHeight: "100vh", background: "#f7f3ef", transition: "margin-left 0.25s" }}>
        <Outlet />
      </main>
    </div>
  );
}
