import { useState } from "react";

import { Dashboard } from "./components/Dashboard";
import { ResearchTab } from "./components/research/ResearchTab";

type Tab = "research" | "positions";

function App() {
  const [tab, setTab] = useState<Tab>("research");

  return (
    <>
      <nav className="navbar">
        <span className="brand">merval-ai</span>
        <div className="nav-tabs">
          <button
            className={tab === "research" ? "nav-tab active" : "nav-tab"}
            onClick={() => setTab("research")}
          >
            Research
          </button>
          <button
            className={tab === "positions" ? "nav-tab active" : "nav-tab"}
            onClick={() => setTab("positions")}
          >
            Positions
          </button>
        </div>
      </nav>
      <main className="app-main">
        {tab === "research" ? <ResearchTab /> : <Dashboard />}
      </main>
    </>
  );
}

export default App;
