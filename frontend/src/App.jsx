import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { ConfigProvider } from "antd";
import { antTheme } from "./styles/theme";
import Layout    from "./components/Layout/Layout";
import Login     from "./pages/Login";
import Overview  from "./pages/Overview";
import TunisiaMap from "./pages/TunisiaMap";
import Analytics  from "./pages/Analytics";
import Scrapers   from "./pages/Scrapers";
import Pipeline   from "./pages/Pipeline";
import Listings   from "./pages/Listings";
import PowerBI    from "./pages/PowerBI";

function AuthGuard({ children }) {
  const location = useLocation();
  const token = localStorage.getItem("em_token");
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

export default function App() {
  return (
    <ConfigProvider theme={antTheme}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<AuthGuard><Layout /></AuthGuard>}>
            <Route index          element={<Overview />} />
            <Route path="map"     element={<TunisiaMap />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="scrapers"  element={<Scrapers />} />
            <Route path="pipeline"  element={<Pipeline />} />
            <Route path="listings"  element={<Listings />} />
            <Route path="powerbi"   element={<PowerBI />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
