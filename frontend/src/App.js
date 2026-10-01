import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Layout from "@/components/Layout";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import VerifyEmail from "@/pages/VerifyEmail";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import AcceptInvite from "@/pages/AcceptInvite";
import Dashboard from "@/pages/Dashboard";
import Sites from "@/pages/Sites";
import Vault from "@/pages/Vault";
import Labs from "@/pages/Labs";
import Analytics from "@/pages/Analytics";
import Team from "@/pages/Team";
import Notifications from "@/pages/Notifications";
import Admin from "@/pages/Admin";

const wrap = (el, roles) => (
  <ProtectedRoute roles={roles}>
    <Layout>{el}</Layout>
  </ProtectedRoute>
);

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify-email/:token" element={<VerifyEmail />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="/invite/:token" element={<AcceptInvite />} />
            <Route path="/dashboard" element={wrap(<Dashboard />)} />
            <Route path="/sites" element={wrap(<Sites />)} />
            <Route path="/vault" element={wrap(<Vault />)} />
            <Route path="/lab" element={wrap(<Labs />)} />
            <Route path="/analitik" element={wrap(<Analytics />)} />
            <Route path="/tim" element={wrap(<Team />, ["company_admin", "swarna_admin"])} />
            <Route path="/notifikasi" element={wrap(<Notifications />)} />
            <Route path="/admin" element={wrap(<Admin />, ["swarna_admin"])} />
          </Routes>
        </BrowserRouter>
        <Toaster richColors position="top-right" />
      </AuthProvider>
    </div>
  );
}

export default App;
