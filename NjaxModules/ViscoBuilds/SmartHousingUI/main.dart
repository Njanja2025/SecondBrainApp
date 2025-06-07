import 'package:flutter/material.dart';

void main() => runApp(SmartHousingApp());

class SmartHousingApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NjaxCitizen Smart Housing',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: SmartHousingHome(),
    );
  }
}

class SmartHousingHome extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Smart Housing Dashboard')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: Icon(Icons.home, color: Colors.green),
              title: Text('Rent Status'),
              subtitle: Text('Paid until: 2025-07-01'),
              trailing: Icon(Icons.check_circle, color: Colors.green),
            ),
          ),
          SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _SmartMeterWidget(type: 'Electric', value: 72, unit: '%'),
              _SmartMeterWidget(type: 'Water', value: 55, unit: '%'),
            ],
          ),
          SizedBox(height: 24),
          ElevatedButton.icon(
            icon: Icon(Icons.build),
            label: Text('Request Maintenance'),
            onPressed: () {
              // TODO: Implement request logic
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Maintenance request sent!')),
              );
            },
          ),
          SizedBox(height: 24),
          Text('Family Members', style: Theme.of(context).textTheme.headline6),
          _FamilyMemberList(),
        ],
      ),
    );
  }
}

class _SmartMeterWidget extends StatelessWidget {
  final String type;
  final int value;
  final String unit;
  const _SmartMeterWidget({required this.type, required this.value, required this.unit});
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(type, style: TextStyle(fontWeight: FontWeight.bold)),
        SizedBox(height: 8),
        Stack(
          alignment: Alignment.center,
          children: [
            SizedBox(
              width: 60,
              height: 60,
              child: CircularProgressIndicator(
                value: value / 100,
                strokeWidth: 8,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(type == 'Electric' ? Colors.orange : Colors.blue),
              ),
            ),
            Text('$value$unit'),
          ],
        ),
      ],
    );
  }
}

class _FamilyMemberList extends StatelessWidget {
  final List<Map<String, String>> members = [
    {'name': 'Alice', 'role': 'Parent'},
    {'name': 'Bob', 'role': 'Child'},
    {'name': 'Eve', 'role': 'Grandparent'},
  ];
  @override
  Widget build(BuildContext context) {
    return Column(
      children: members.map((m) => ListTile(
        leading: Icon(Icons.person),
        title: Text(m['name']!),
        subtitle: Text(m['role']!),
        trailing: IconButton(
          icon: Icon(Icons.remove_circle, color: Colors.red),
          onPressed: () {
            // TODO: Remove member logic
          },
        ),
      )).toList(),
    );
  }
}
