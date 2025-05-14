import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  RefreshControl,
  Platform,
} from 'react-native';
import {
  LineChart,
  BarChart,
  PieChart,
} from 'react-native-chart-kit';
import { Dimensions } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useColorScheme } from 'react-native';

const screenWidth = Dimensions.get('window').width;

const App = () => {
  const [metrics, setMetrics] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const isDarkMode = useColorScheme() === 'dark';

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    fetchMetrics().then(() => setRefreshing(false));
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartConfig = {
    backgroundGradientFrom: darkMode ? '#1a1a1a' : '#ffffff',
    backgroundGradientTo: darkMode ? '#1a1a1a' : '#ffffff',
    color: (opacity = 1) => darkMode ? `rgba(255, 255, 255, ${opacity})` : `rgba(0, 0, 0, ${opacity})`,
    strokeWidth: 2,
    barPercentage: 0.5,
    useShadowColorFromDataset: false,
  };

  const renderMetrics = () => {
    if (!metrics) return null;

    const cpuData = {
      labels: ['CPU Usage'],
      datasets: [{
        data: [metrics.cpu.percent],
      }],
    };

    const memoryData = {
      labels: ['Memory Usage'],
      datasets: [{
        data: [metrics.memory.percent],
      }],
    };

    const diskData = {
      labels: ['Disk Usage'],
      datasets: [{
        data: [metrics.disk.percent],
      }],
    };

    const networkData = {
      labels: ['Sent', 'Received'],
      datasets: [{
        data: [
          metrics.network.bytes_sent / (1024 * 1024),
          metrics.network.bytes_recv / (1024 * 1024),
        ],
      }],
    };

    return (
      <ScrollView
        style={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, darkMode && styles.darkText]}>CPU Usage</Text>
          <LineChart
            data={cpuData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, darkMode && styles.darkText]}>Memory Usage</Text>
          <BarChart
            data={memoryData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            style={styles.chart}
          />
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, darkMode && styles.darkText]}>Disk Usage</Text>
          <PieChart
            data={[
              {
                name: 'Used',
                population: metrics.disk.percent,
                color: '#FF6384',
                legendFontColor: darkMode ? '#ffffff' : '#000000',
              },
              {
                name: 'Free',
                population: 100 - metrics.disk.percent,
                color: '#36A2EB',
                legendFontColor: darkMode ? '#ffffff' : '#000000',
              },
            ]}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="15"
            style={styles.chart}
          />
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, darkMode && styles.darkText]}>Network Usage</Text>
          <BarChart
            data={networkData}
            width={screenWidth - 40}
            height={220}
            chartConfig={chartConfig}
            style={styles.chart}
          />
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, darkMode && styles.darkText]}>System Info</Text>
          <View style={styles.infoContainer}>
            <Text style={[styles.infoText, darkMode && styles.darkText]}>
              Platform: {metrics.system.platform}
            </Text>
            <Text style={[styles.infoText, darkMode && styles.darkText]}>
              Python Version: {metrics.system.python_version}
            </Text>
            <Text style={[styles.infoText, darkMode && styles.darkText]}>
              Boot Time: {new Date(metrics.system.boot_time).toLocaleString()}
            </Text>
          </View>
        </View>
      </ScrollView>
    );
  };

  return (
    <SafeAreaView style={[styles.container, darkMode && styles.darkContainer]}>
      <StatusBar barStyle={darkMode ? 'light-content' : 'dark-content'} />
      <View style={styles.header}>
        <Text style={[styles.title, darkMode && styles.darkText]}>System Monitor</Text>
        <TouchableOpacity
          style={styles.darkModeButton}
          onPress={() => setDarkMode(!darkMode)}
        >
          <Text style={[styles.darkModeText, darkMode && styles.darkText]}>
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </Text>
        </TouchableOpacity>
      </View>
      {renderMetrics()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  darkContainer: {
    backgroundColor: '#1a1a1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000000',
  },
  darkText: {
    color: '#ffffff',
  },
  darkModeButton: {
    padding: 10,
    borderRadius: 5,
    backgroundColor: '#e0e0e0',
  },
  darkModeText: {
    color: '#000000',
  },
  section: {
    margin: 20,
    padding: 15,
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#000000',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  infoContainer: {
    padding: 10,
  },
  infoText: {
    fontSize: 16,
    marginBottom: 5,
    color: '#000000',
  },
});

export default App; 