import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuth } from '../context/AuthContext';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import MyRidesScreen from '../screens/MyRidesScreen';
import MyRequestsScreen from '../screens/MyRequestsScreen';
import SearchRidesScreen from '../screens/SearchRidesScreen';
import ProfileScreen from '../screens/ProfileScreen';
import CreateRideScreen from '../screens/CreateRideScreen';
import { View, ActivityIndicator, StyleSheet } from 'react-native';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarLabelStyle: { fontSize: 12 },
        headerTitleStyle: { fontSize: 18 },
      }}
    >
      <Tab.Screen
        name="MyRides"
        component={MyRidesScreen}
        options={{ title: 'הנסיעות שלי', tabBarLabel: 'נהג' }}
      />
      <Tab.Screen
        name="SearchRides"
        component={SearchRidesScreen}
        options={{ title: 'חיפוש נסיעות', tabBarLabel: 'חיפוש' }}
      />
      <Tab.Screen
        name="MyRequests"
        component={MyRequestsScreen}
        options={{ title: 'הבקשות שלי', tabBarLabel: 'נוסע' }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ title: 'פרופיל', tabBarLabel: 'פרופיל' }}
      />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? (
        <Stack.Navigator screenOptions={{ headerShown: true, headerTitleStyle: { fontSize: 18 } }}>
          <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
          <Stack.Screen name="CreateRide" component={CreateRideScreen} options={{ title: 'יצירת נסיעה' }} />
        </Stack.Navigator>
      ) : (
        <Stack.Navigator
          screenOptions={{
            headerShown: true,
            headerTitleStyle: { fontSize: 18 },
          }}
        >
          <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'התחברות' }} />
          <Stack.Screen name="Register" component={RegisterScreen} options={{ title: 'הרשמה' }} />
        </Stack.Navigator>
      )}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});
