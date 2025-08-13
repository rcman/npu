import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.List;

public class NetworkHardwareScanner extends JFrame {
    private DefaultTableModel tableModel;
    private JTable deviceTable;
    private JButton scanButton;
    private JProgressBar progressBar;

    public NetworkHardwareScanner() {
        super("Network Hardware Scanner");
        setupUI();
        setSize(800, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
    }

    private void setupUI() {
        // Create table model
        String[] columns = {"IP Address", "Hostname", "CPU Cores", "Total Memory", "Disk Space"};
        tableModel = new DefaultTableModel(columns, 0);
        deviceTable = new JTable(tableModel);
        deviceTable.setAutoCreateRowSorter(true);

        // Create scan button
        scanButton = new JButton("Scan Network");
        scanButton.addActionListener(e -> startNetworkScan());

        // Create progress bar
        progressBar = new JProgressBar(0, 100);
        progressBar.setStringPainted(true);

        // Layout
        JPanel controlPanel = new JPanel(new BorderLayout());
        controlPanel.add(scanButton, BorderLayout.NORTH);
        controlPanel.add(progressBar, BorderLayout.SOUTH);

        add(controlPanel, BorderLayout.NORTH);
        add(new JScrollPane(deviceTable), BorderLayout.CENTER);
    }

    private void startNetworkScan() {
        tableModel.setRowCount(0);
        scanButton.setEnabled(false);
        progressBar.setValue(0);

        new SwingWorker<Void, MachineInfo>() {
            @Override
            protected Void doInBackground() {
                try {
                    String baseIp = getLocalBaseIP();
                    List<String> activeIps = new ArrayList<>();
                    
                    // Ping sweep (first 10 IPs for demo - adjust as needed)
                    int totalIps = 10;
                    for (int i = 1; i <= totalIps; i++) {
                        String ip = baseIp + i;
                        if (InetAddress.getByName(ip).isReachable(500)) {
                            activeIps.add(ip);
                        }
                        setProgress(i * 100 / totalIps);
                    }
                    
                    // Collect hardware info
                    for (int i = 0; i < activeIps.size(); i++) {
                        MachineInfo info = gatherHardwareInfo(activeIps.get(i));
                        publish(info);
                        setProgress((i + 1) * 100 / activeIps.size());
                    }
                } catch (Exception ex) {
                    ex.printStackTrace();
                }
                return null;
            }

            @Override
            protected void process(List<MachineInfo> chunks) {
                for (MachineInfo info : chunks) {
                    Object[] row = {
                        info.ip,
                        info.hostname,
                        info.cpuCores,
                        info.totalMemory + " GB",
                        info.diskSpace + " GB"
                    };
                    tableModel.addRow(row);
                }
            }

            @Override
            protected void done() {
                scanButton.setEnabled(true);
                progressBar.setValue(100);
            }
        }.execute();
    }

    private String getLocalBaseIP() throws Exception {
        InetAddress localHost = InetAddress.getLocalHost();
        String hostAddress = localHost.getHostAddress();
        return hostAddress.substring(0, hostAddress.lastIndexOf('.') + 1);
    }

    private MachineInfo gatherHardwareInfo(String ip) {
        MachineInfo info = new MachineInfo();
        info.ip = ip;
        
        try {
            // SSH command to retrieve hardware info
            Process process = Runtime.getRuntime().exec(new String[]{
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                ip,
                "sh -c 'hostname; nproc; free -g | awk \"/Mem/ {print \\$2}\"; df -BG / | awk \"NR>1 {print \\$2}\" | tr -d \"G\"'"
            });
            
            try (BufferedReader reader = new BufferedReader(
                 new InputStreamReader(process.getInputStream()))) {
                
                info.hostname = reader.readLine().trim();
                info.cpuCores = Integer.parseInt(reader.readLine().trim());
                info.totalMemory = Integer.parseInt(reader.readLine().trim());
                info.diskSpace = Integer.parseInt(reader.readLine().trim());
            }
        } catch (Exception e) {
            info.hostname = "N/A";
        }
        return info;
    }

    static class MachineInfo {
        String ip;
        String hostname;
        int cpuCores;
        int totalMemory;
        int diskSpace;
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new NetworkHardwareScanner().setVisible(true));
    }
}