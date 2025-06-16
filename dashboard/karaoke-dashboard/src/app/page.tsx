import UploadPanel from "../components/UploadPanel";
import MetricsPanel from "../components/MetricsPanel";
import SettingsPanel from "../components/SettingsPanel";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-8">
      <UploadPanel />
      <MetricsPanel />
      <SettingsPanel />
    </div>
  );
}
