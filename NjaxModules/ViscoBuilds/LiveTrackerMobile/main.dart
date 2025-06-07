import 'package:flutter/material.dart';

void main() => runApp(NjaxLiveTrackerApp());

class NjaxLiveTrackerApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Njax Live Tracker',
      theme: ThemeData(primarySwatch: Colors.teal),
      home: LiveTrackerHome(),
    );
  }
}

class LiveTrackerHome extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Njax Live Tracker')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          _SectionTitle('Njax Intelligence Updates'),
          _InfoCard(icon: Icons.insights, label: 'AI says: All clear!'),
          SizedBox(height: 16),
          _SectionTitle('City Alerts'),
          _InfoCard(icon: Icons.warning, label: 'No current alerts'),
          SizedBox(height: 16),
          _SectionTitle('Wallet Balance'),
          _InfoCard(icon: Icons.account_balance_wallet, label: 'Ξ 0.42 (Web3 Ready)'),
          SizedBox(height: 16),
          _SectionTitle('Smart City Score'),
          _InfoCard(icon: Icons.emoji_events, label: 'Score: 87/100'),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Text(text, style: Theme.of(context).textTheme.headline6),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String label;
  const _InfoCard({required this.icon, required this.label});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon, size: 36, color: Colors.teal),
        title: Text(label),
      ),
    );
  }
}
