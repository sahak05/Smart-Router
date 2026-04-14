<template>
  <v-app>
    <v-navigation-drawer permanent rail expand-on-hover>
      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-router-network"
          title="Devices"
          value="devices"
          active
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-record-circle-outline"
          title="Captures"
          value="captures"
        ></v-list-item>
        <v-list-item prepend-icon="mdi-wall" title="Firewall" value="firewall"></v-list-item>
        <v-list-item
          prepend-icon="mdi-chart-timeline-variant"
          title="Metrics"
          value="metrics"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar color="surface-variant" elevation="1" density="compact">
      <v-app-bar-title>Smart Router</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon="mdi-shield-check" color="success"></v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height align-start">
        <v-row class="fill-height">
          <v-col cols="4" class="border-e">
            <div class="d-flex align-center justify-space-between mb-4 px-2">
              <h2 class="text-h6">Connected Devices</h2>
              <v-btn icon="mdi-refresh" variant="text" size="small" @click="fetchDevices"></v-btn>
            </div>

            <v-list lines="two" bg-color="transparent">
              <v-list-item
                v-for="device in devices"
                :key="device.mac"
                :title="device.custom_name || device.vendor || 'Unknown Device'"
                :subtitle="device.ip"
                :prepend-icon="getDeviceIcon(device.device_type)"
                :active="selectedDevice?.mac === device.mac"
                color="primary"
                rounded="lg"
                class="mb-2"
                @click="selectDevice(device)"
              ></v-list-item>
            </v-list>
          </v-col>

          <v-col cols="8" class="pa-6">
            <div v-if="selectedDevice">
              <v-card elevation="0" color="transparent">
                <v-card-title class="text-h5 px-0 mb-4">Device Configuration</v-card-title>

                <v-card-text class="px-0">
                  <v-row>
                    <v-col cols="6">
                      <v-text-field
                        v-model="selectedDevice.ip"
                        label="IP Address"
                        readonly
                        variant="outlined"
                        density="comfortable"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="6">
                      <v-text-field
                        v-model="selectedDevice.mac"
                        label="MAC Address"
                        readonly
                        variant="outlined"
                        density="comfortable"
                      ></v-text-field>
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="6">
                      <v-text-field
                        v-model="selectedDevice.custom_name"
                        label="Custom Name"
                        placeholder="e.g. Abdoul's Phone"
                        variant="outlined"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="6">
                      <v-select
                        v-model="selectedDevice.device_type"
                        label="Device Type"
                        :items="['Mobile', 'Laptop', 'IoT', 'TV', 'Unknown']"
                        variant="outlined"
                      >
                      </v-select>
                    </v-col>
                  </v-row>
                </v-card-text>

                <v-card-actions class="px-0 mt-4">
                  <v-btn
                    color="primary"
                    variant="flat"
                    prepend-icon="mdi-content-save"
                    size="large"
                    @click="saveDeviceChanges"
                    >Save Changes</v-btn
                  >
                  <v-spacer></v-spacer>
                  <v-btn color="error" variant="tonal" prepend-icon="mdi-block-helper"
                    >Block Device</v-btn
                  >
                </v-card-actions>
              </v-card>
            </div>

            <div
              v-else
              class="d-flex flex-column align-center justify-center fill-height text-medium-emphasis"
            >
              <v-icon size="64" class="mb-4">mdi-gesture-tap</v-icon>
              <p>Select a device from the list to view and configure its network access.</p>
            </div>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// Empty array that will hold your real database records
const devices = ref([])
const selectedDevice = ref(null)

// The engine that pulls data from your Python API
const fetchDevices = async () => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/devices')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    devices.value = data
  } catch (error) {
    console.error('Error fetching live device data:', error)
  }
}

onMounted(() => {
  fetchDevices()
})

const selectDevice = (device) => {
  selectedDevice.value = device
}

const getDeviceIcon = (type) => {
  const icons = {
    Mobile: 'mdi-cellphone',
    Laptop: 'mdi-laptop',
    TV: 'mdi-television',
    IoT: 'mdi-home-lightbulb',
    Unknown: 'mdi-help-network'
  }
  return icons[type] || icons['Unknown']
}

const saveDeviceChanges = async () => {
  if (!selectedDevice.value) return

  try {
    const response = await fetch(`http://127.0.0.1:5000/api/devices/${selectedDevice.value.mac}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        custom_name: selectedDevice.value.custom_name,
        device_type: selectedDevice.value.device_type
      })
    })

    if (response.ok) {
      console.log('Device successfully updated!')
      // Automatically refresh the list on the left to show the new name
      fetchDevices()
    } else {
      console.error('Failed to update device.')
    }
  } catch (error) {
    console.error('Error saving changes:', error)
  }
}
</script>

<style scoped>
.border-e {
  border-right: 1px solid rgba(255, 255, 255, 0.12);
}
</style>
