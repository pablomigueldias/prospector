import { Sidebar } from '@/components/shared/Sidebar';
import { Topbar } from '@/components/shared/Topbar';

interface DashboardLayoutProps {
  children: React.ReactNode;
  currentAgentName?: string | null;
}

export function DashboardLayout({
  children,
  currentAgentName,
}: DashboardLayoutProps) {
  return (
    <div className="grid grid-cols-[240px_1fr] h-screen bg-bg">
      <Sidebar />
      <div className="flex flex-col min-w-0">
        <Topbar currentAgentName={currentAgentName} />
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  );
}
