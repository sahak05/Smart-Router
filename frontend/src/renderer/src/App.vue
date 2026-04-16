<template>
  <v-app>
    <v-navigation-drawer permanent rail expand-on-hover>
      <v-list
        v-model:selected="currentMenuSelection"
        density="compact"
        nav
        @update:selected="changeView"
      >
        <v-list-item
          prepend-icon="mdi-router-network"
          title="Devices"
          value="devices"
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
      <v-app-bar-title
        >Smart Router Admin
        <span class="text-caption text-medium-emphasis ml-2"
          >| {{ currentView.toUpperCase() }}</span
        ></v-app-bar-title
      >
      <v-spacer></v-spacer>
      <v-btn icon="mdi-shield-check" color="success"></v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height align-start">
        <v-row v-if="currentView === 'devices'" class="fill-height">
          <v-col cols="4" class="border-e">
            <div class="d-flex align-center justify-space-between mb-4 px-2">
              <h2 class="text-h6">Connected Devices</h2>
              <v-btn icon="mdi-refresh" variant="text" size="small" @click="fetchDevices"></v-btn>
            </div>
            <v-list lines="two" bg-color="transparent">
              <v-list-item
                v-for="device in devices"
                :key="device.mac_address"
                :title="device.custom_name || device.vendor || 'Unknown Device'"
                :subtitle="device.ip_address"
                :prepend-icon="getDeviceIcon(device.device_type)"
                :active="selectedDevice?.mac_address === device.mac_address"
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
                    <v-col cols="6"
                      ><v-text-field
                        v-model="selectedDevice.ip_address"
                        label="IP Address"
                        readonly
                        variant="outlined"
                      ></v-text-field
                    ></v-col>
                    <v-col cols="6"
                      ><v-text-field
                        v-model="selectedDevice.mac_address"
                        label="MAC Address"
                        readonly
                        variant="outlined"
                      ></v-text-field
                    ></v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="6"
                      ><v-text-field
                        v-model="selectedDevice.custom_name"
                        label="Custom Name"
                        variant="outlined"
                      ></v-text-field
                    ></v-col>
                    <v-col cols="6">
                      <v-select
                        v-model="selectedDevice.device_type"
                        label="Device Type"
                        :items="['Mobile', 'Laptop', 'IoT', 'TV', 'Unknown']"
                        variant="outlined"
                      ></v-select>
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
                  <v-btn
                    :color="isDeviceAuthorized ? 'error' : 'success'"
                    variant="tonal"
                    :prepend-icon="
                      isDeviceAuthorized ? 'mdi-block-helper' : 'mdi-check-network-outline'
                    "
                    @click="toggleDeviceAccess"
                  >
                    {{ isDeviceAuthorized ? 'Block Device (Revoke)' : 'Authorize Device' }}
                  </v-btn>
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

        <v-row v-else-if="currentView === 'captures'" class="fill-height">
          <v-col cols="4" class="border-e">
            <h2 class="text-h6 mb-4 px-2">Capture Targets</h2>
            <v-list lines="two" bg-color="transparent">
              <v-list-item
                v-for="device in devices"
                :key="device.mac_address"
                :title="device.custom_name || device.vendor || 'Unknown Device'"
                :subtitle="device.ip_address"
                prepend-icon="mdi-target"
                :active="selectedCaptureDevice?.mac_address === device.mac_address"
                color="error"
                rounded="lg"
                class="mb-2"
                @click="selectedCaptureDevice = device"
              ></v-list-item>
            </v-list>
          </v-col>

          <v-col cols="8" class="pa-6">
            <div v-if="selectedCaptureDevice">
              <v-card elevation="0" color="transparent">
                <v-card-title class="text-h5 px-0 text-error">TShark Intercept Engine</v-card-title>
                <v-card-text class="px-0 mt-4">
                  <p class="text-body-1 mb-6">
                    Configure the background TShark intercept for
                    <strong>{{ selectedCaptureDevice.ip_address }}</strong
                    >.
                  </p>
                  <br />
                  <v-row class="mb-4">
                    <v-col cols="4">
                      <v-select
                        v-model="captureSettings.type"
                        label="Limit Capture By"
                        :items="[
                          { title: 'Time (Duration)', value: 'duration' },
                          { title: 'Packet Count', value: 'packets' }
                        ]"
                        variant="outlined"
                        density="compact"
                      ></v-select>
                    </v-col>
                    <v-col cols="4">
                      <v-text-field
                        v-model="captureSettings.value"
                        :label="captureSettings.type === 'duration' ? 'Seconds' : 'Max Packets'"
                        type="number"
                        variant="outlined"
                        density="compact"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="4">
                      <v-text-field
                        v-model="captureSettings.filename"
                        label="Custom Filename"
                        placeholder="Auto-generated if blank"
                        variant="outlined"
                        density="compact"
                      ></v-text-field>
                    </v-col>
                  </v-row>

                  <div class="d-flex gap-4">
                    <v-btn
                      color="error"
                      variant="flat"
                      size="large"
                      prepend-icon="mdi-record-circle"
                      @click="startCapture"
                      >Start Capture</v-btn
                    >
                    <v-btn
                      color="surface-variant"
                      variant="flat"
                      size="large"
                      prepend-icon="mdi-stop-circle"
                      class="ml-4"
                      @click="stopCapture"
                      >Stop Capture</v-btn
                    >
                  </div>
                </v-card-text>
              </v-card>
            </div>
            <div
              v-else
              class="d-flex flex-column align-center justify-center fill-height text-medium-emphasis"
            >
              <v-icon size="64" class="mb-4">mdi-radar</v-icon>
              <p>Select a target device to initialize packet capture.</p>
            </div>
          </v-col>
        </v-row>

        <v-row v-else-if="currentView === 'firewall'" class="fill-height">
          <v-col cols="12" class="pa-6">
            <div class="d-flex align-center justify-space-between mb-4">
              <h2 class="text-h5">Firewall Management</h2>
              <v-btn
                color="primary"
                variant="tonal"
                prepend-icon="mdi-refresh"
                @click="fetchFirewallRules"
                >Refresh Database</v-btn
              >
            </div>

            <v-card class="mb-8 border" elevation="0" color="surface">
              <v-card-title class="text-subtitle-1 border-b">Add Custom Rule</v-card-title>
              <v-card-text class="pt-4">
                <v-form @submit.prevent="addCustomRule">
                  <v-row>
                    <v-col cols="3">
                      <v-text-field
                        v-model="newRule.src_ip"
                        label="Source IP"
                        placeholder="e.g. 192.168.137.39"
                        variant="outlined"
                        density="compact"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="3">
                      <v-text-field
                        v-model="newRule.dest_ip"
                        label="Destination IP"
                        placeholder="ANY or 8.8.8.8"
                        variant="outlined"
                        density="compact"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="2">
                      <v-text-field
                        v-model="newRule.dest_port"
                        label="Dest Port"
                        placeholder="ANY or 443"
                        variant="outlined"
                        density="compact"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="4">
                      <v-text-field
                        v-model="newRule.description"
                        label="Description"
                        placeholder="e.g. Allow Web Traffic"
                        variant="outlined"
                        density="compact"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                  <v-btn type="submit" color="success" prepend-icon="mdi-plus" class="mt-2"
                    >Create Rule</v-btn
                  >
                </v-form>
              </v-card-text>
            </v-card>

            <h3 class="text-h6 mb-3">Active Allow-List Rules</h3>
            <v-table theme="dark" class="bg-surface-variant rounded-lg">
              <thead>
                <tr>
                  <th class="text-left">Source IP</th>
                  <th class="text-left">Destination IP</th>
                  <th class="text-left">Port</th>
                  <th class="text-left">Description</th>
                  <th class="text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rule in firewallRules" :key="rule.id">
                  <td class="text-success font-weight-bold">{{ rule.src_ip }}</td>
                  <td>{{ rule.dest_ip }}</td>
                  <td class="text-warning">{{ rule.dest_port }}</td>
                  <td>{{ rule.description }}</td>
                  <td class="text-center">
                    <v-btn
                      icon="mdi-delete"
                      color="error"
                      variant="text"
                      size="small"
                      @click="deleteRule(rule.src_ip)"
                    ></v-btn>
                  </td>
                </tr>
                <tr v-if="firewallRules.length === 0">
                  <td colspan="5" class="text-center pa-4 text-medium-emphasis">
                    No firewall rules found. System is in Total Lockdown.
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>
        <MetricsDashboard v-if="currentView === 'metrics'" />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import MetricsDashboard from './components/MetricsDashboard.vue' // <<< NEW IMPORT

// --- NAVIGATION STATE ---
const currentMenuSelection = ref(['devices'])
const currentView = ref('devices')

const changeView = (newSelection) => {
  if (newSelection.length > 0) {
    currentView.value = newSelection[0]
  }
}

// --- DATA STATES ---
const devices = ref([])
const selectedDevice = ref(null)
const selectedCaptureDevice = ref(null)
const firewallRules = ref([])

const captureSettings = ref({ type: 'duration', value: 60, filename: '' })
const newRule = ref({ src_ip: '', dest_ip: 'ANY', dest_port: 'ANY', description: '' })

// --- API FETCH FUNCTIONS ---
const fetchDevices = async () => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/devices')
    devices.value = await response.json()
  } catch (error) {
    console.error(error)
  }
}

const fetchFirewallRules = async () => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/firewall')
    firewallRules.value = await response.json()
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  fetchDevices()
  fetchFirewallRules()
})

// --- DEVICE FUNCTIONS ---
const selectDevice = (device) => {
  selectedDevice.value = device
}

const saveDeviceChanges = async () => {
  if (!selectedDevice.value) return
  try {
    await fetch(`http://127.0.0.1:5000/api/devices/${selectedDevice.value.mac_address}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        custom_name: selectedDevice.value.custom_name,
        device_type: selectedDevice.value.device_type
      })
    })
    fetchDevices()
  } catch (error) {
    console.error(error)
  }
}

// --- FIREWALL FUNCTIONS ---
const isDeviceAuthorized = computed(() => {
  if (!selectedDevice.value) return false
  return firewallRules.value.some((rule) => rule.src_ip === selectedDevice.value.ip_address)
})

const toggleDeviceAccess = async () => {
  if (!selectedDevice.value) return
  const ip = selectedDevice.value.ip_address
  try {
    if (isDeviceAuthorized.value) {
      await deleteRule(ip)
    } else {
      await fetch('http://127.0.0.1:5000/api/firewall', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          src_ip: ip,
          dest_ip: 'ANY',
          dest_port: 'ANY',
          description: `Auto-Allowed: ${selectedDevice.value.custom_name || selectedDevice.value.vendor}`
        })
      })
    }
    fetchFirewallRules()
  } catch (error) {
    console.error(error)
  }
}

const addCustomRule = async () => {
  if (!newRule.value.src_ip) return
  try {
    await fetch('http://127.0.0.1:5000/api/firewall', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newRule.value)
    })
    fetchFirewallRules()
    newRule.value = { src_ip: '', dest_ip: 'ANY', dest_port: 'ANY', description: '' }
  } catch (error) {
    console.error('Error creating rule:', error)
  }
}

const deleteRule = async (ip) => {
  try {
    await fetch(`http://127.0.0.1:5000/api/firewall/${ip}`, { method: 'DELETE' })
    fetchFirewallRules()
  } catch (error) {
    console.error(error)
  }
}

// --- CAPTURE FUNCTIONS ---
const startCapture = async () => {
  if (!selectedCaptureDevice.value) return
  try {
    const payload = {
      mac: selectedCaptureDevice.value.mac_address,
      ip: selectedCaptureDevice.value.ip_address,
      type: captureSettings.value.type,
      value: captureSettings.value.value,
      filename: captureSettings.value.filename
    }
    await fetch('http://127.0.0.1:5000/api/captures/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    alert(`Capture initiated for ${payload.ip}. Intercepting for ${payload.value} ${payload.type}.`)
    captureSettings.value.filename = ''
  } catch (error) {
    console.error('Failed to start capture:', error)
  }
}

const stopCapture = async () => {
  if (!selectedCaptureDevice.value) return
  try {
    await fetch('http://127.0.0.1:5000/api/captures/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mac: selectedCaptureDevice.value.mac_address })
    })
    alert(`Capture stopped for ${selectedCaptureDevice.value.ip_address}`)
  } catch (error) {
    console.error(error)
  }
}

// --- UTILS ---
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
</script>

<style scoped>
.border-e {
  border-right: 1px solid rgba(255, 255, 255, 0.12);
}
</style>
