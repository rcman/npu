import { useState, useEffect, useContext, createContext } from 'react';
import { useId } from 'react';

// Use a CSS file for custom styles if needed, but for this example, we'll use Tailwind.
// The provided environment assumes Tailwind is available without an explicit import.
import { Play, Loader, Check, CircleX } from 'lucide-react'; // Example icons for status

// Use this for a context to manage state globally if the app were to grow.
const AppContext = createContext();

// This is the main component of our application.
export default function App() {
  const [machines, setMachines] = useState([]);
  const [status, setStatus] = useState('idle'); // 'idle', 'scanning', 'installing'
  const [scanProgress, setScanProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');

  // Simulates a backend API call to discover Linux machines on the network.
  const discoverMachines = async () => {
    setStatus('scanning');
    setStatusMessage('Scanning for Linux machines...');
    setScanProgress(0);

    // Placeholder for a real network scan. In a real app, a backend server would
    // perform a network sweep (e.g., pinging a range of IPs) and return a list.
    const fakeMachines = [
      { id: useId(), ip: '192.168.1.101', hostname: 'linux-server-1', status: 'pending' },
      { id: useId(), ip: '192.168.1.102', hostname: 'ubuntu-desktop', status: 'pending' },
      { id: useId(), ip: '192.168.1.103', hostname: 'pi-hole', status: 'pending' },
    ];

    // Simulate network latency
    const scanSteps = fakeMachines.length + 1;
    for (let i = 0; i < scanSteps; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setScanProgress(Math.floor((i / scanSteps) * 100));
    }
    
    setMachines(fakeMachines);
    setStatus('idle');
    setStatusMessage('Scan complete. Found machines.');
  };

  // Simulates an MPI installation on a remote machine.
  const installMPI = async (machineId) => {
    const updatedMachines = machines.map(m =>
      m.id === machineId ? { ...m, status: 'installing', specs: 'Fetching...' } : m
    );
    setMachines(updatedMachines);
    setStatus('installing');
    setStatusMessage('Installing MPI on remote machine...');

    // In a real application, this would make a secure API call to a backend server.
    // The backend would use SSH to connect to the machine, run `sudo apt-get install openmpi-bin`,
    // and fetch the system specifications.
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Simulate fetching machine specs after installation.
    const specs = {
      os: 'Linux 5.15.0-101-generic',
      cpu: 'AMD Ryzen 7 5800X 8-Core',
      memory: '32 GB DDR4',
    };

    const finalMachines = updatedMachines.map(m =>
      m.id === machineId ? { ...m, status: 'installed', specs: specs } : m
    );
    setMachines(finalMachines);
    setStatus('idle');
    setStatusMessage('Installation complete.');
  };

  const isScanning = status === 'scanning';
  const isInstalling = status === 'installing';

  return (
    <div className="min-h-screen bg-slate-900 text-gray-100 p-8 font-sans">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-extrabold text-blue-400 drop-shadow-lg">MPI Manager</h1>
        <p className="text-gray-400 mt-2">Remote MPI Installation and Monitoring Dashboard</p>
      </header>
      
      <main className="container mx-auto max-w-5xl bg-slate-800 rounded-2xl shadow-xl p-6 md:p-10">
        <div className="flex flex-col md:flex-row items-center justify-between mb-8 space-y-4 md:space-y-0">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-200">Discovered Machines</h2>
            <p className="text-sm text-gray-400 mt-1">{statusMessage || 'Click "Scan Network" to begin.'}</p>
          </div>
          <div className="flex-shrink-0">
            <button
              onClick={discoverMachines}
              disabled={isScanning || isInstalling}
              className={`flex items-center px-6 py-3 rounded-full font-semibold transition-all duration-300 transform-gpu
                ${isScanning || isInstalling ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600 text-white shadow-lg hover:scale-105'}`}
            >
              <Play className="w-5 h-5 mr-2" />
              Scan Network
            </button>
          </div>
        </div>

        {/* Progress bar for scanning */}
        {isScanning && (
          <div className="w-full bg-gray-600 rounded-full h-2.5 mb-4">
            <div className="bg-blue-400 h-2.5 rounded-full transition-all duration-300" style={{ width: `${scanProgress}%` }}></div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead>
              <tr className="bg-slate-700">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider rounded-tl-lg">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Hostname</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">IP Address</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Specifications</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider rounded-tr-lg">Action</th>
              </tr>
            </thead>
            <tbody className="bg-slate-800 divide-y divide-gray-700">
              {machines.length > 0 ? (
                machines.map((machine) => (
                  <tr key={machine.id} className="hover:bg-slate-700 transition-colors duration-200">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      <div className="flex items-center space-x-2">
                        {machine.status === 'pending' && <Loader className="w-4 h-4 text-yellow-500 animate-spin" />}
                        {machine.status === 'installing' && <Loader className="w-4 h-4 text-blue-400 animate-spin" />}
                        {machine.status === 'installed' && <Check className="w-4 h-4 text-green-500" />}
                        {machine.status === 'error' && <CircleX className="w-4 h-4 text-red-500" />}
                        <span className="capitalize">{machine.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-200">{machine.hostname}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{machine.ip}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {machine.specs ? (
                        <div className="flex flex-col space-y-1">
                          <span><span className="font-semibold text-gray-400">OS:</span> {machine.specs.os}</span>
                          <span><span className="font-semibold text-gray-400">CPU:</span> {machine.specs.cpu}</span>
                          <span><span className="font-semibold text-gray-400">Memory:</span> {machine.specs.memory}</span>
                        </div>
                      ) : (
                        <span className="text-gray-500">Not available</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {machine.status === 'pending' && (
                        <button
                          onClick={() => installMPI(machine.id)}
                          disabled={isInstalling || isScanning}
                          className="text-blue-400 hover:text-blue-500 transition-colors duration-200 disabled:text-gray-500 disabled:cursor-not-allowed"
                        >
                          Install MPI
                        </button>
                      )}
                      {machine.status === 'installing' && (
                        <span className="text-gray-500">Installing...</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                    No machines found. Please scan the network.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
