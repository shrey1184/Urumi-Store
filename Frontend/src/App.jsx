import { Toaster } from "react-hot-toast";
import Dashboard from "./pages/Dashboard";
import "./App.css";

function App() {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            borderRadius: "8px",
            background: "#1e1e2e",
            color: "#cdd6f4",
            fontSize: "14px",
          },
        }}
      />
      <Dashboard />
    </>
  );
}

export default App;
