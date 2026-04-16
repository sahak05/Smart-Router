<template>
  <v-row class="fill-height">
    <v-col cols="12" class="pa-6">
      <div class="d-flex align-center justify-space-between mb-6">
        <h2 class="text-h5">Network Telemetry</h2>
        <v-btn color="primary" prepend-icon="mdi-refresh" @click="fetchMetrics"
          >Refresh Telemetry</v-btn
        >
      </div>

      <v-row>
        <v-col cols="4">
          <v-card color="surface-variant" elevation="0" class="pa-4 border text-center">
            <div class="text-subtitle-2 text-medium-emphasis text-uppercase">Total Devices</div>
            <div class="text-h3 font-weight-bold mt-2 text-primary">
              {{ metrics.total_devices || 0 }}
            </div>
          </v-card>
        </v-col>
        <v-col cols="4">
          <v-card color="error" variant="tonal" elevation="0" class="pa-4 border text-center">
            <div class="text-subtitle-2 text-uppercase">Active IPS Throttles</div>
            <div class="text-h3 font-weight-bold mt-2">{{ metrics.throttled_devices || 0 }}</div>
          </v-card>
        </v-col>
        <v-col cols="4">
          <v-card color="success" variant="tonal" elevation="0" class="pa-4 border text-center">
            <div class="text-subtitle-2 text-uppercase">Kernel Firewall Rules</div>
            <div class="text-h3 font-weight-bold mt-2">{{ metrics.total_rules || 0 }}</div>
          </v-card>
        </v-col>
      </v-row>

      <h3 class="text-h6 mt-8 mb-4">Device Threshold Allocations (Pkts / 10s)</h3>
      <v-card elevation="0" class="border bg-surface-variant pa-6">
        <div v-for="dev in metrics.devices_data" :key="dev.ip_address" class="mb-5">
          <div class="d-flex justify-space-between mb-2">
            <span class="font-weight-medium">{{ dev.custom_name || dev.ip_address }}</span>
            <span class="text-medium-emphasis">{{ dev.threshold }} Limit</span>
          </div>
          <v-progress-linear
            :model-value="(dev.threshold / 1000) * 100"
            color="primary"
            height="12"
            rounded
            striped
          ></v-progress-linear>
        </div>
        <div v-if="!metrics.devices_data?.length" class="text-medium-emphasis text-center pa-4">
          No active devices found to visualize.
        </div>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const metrics = ref({})
let refreshInterval = null

// Component-specific fetch logic
const fetchMetrics = async () => {
  try {
    const response = await fetch('http://127.0.0.1:5000/api/metrics')
    metrics.value = await response.json()
  } catch (error) {
    console.error('Metrics Fetch Error:', error)
  }
}

onMounted(() => {
  // Fetch immediately when the component loads
  fetchMetrics()
  refreshInterval = setInterval(fetchMetrics, 5000)
})

onUnmounted(() => {
  // Clean up the timer if we navigate away from the tab
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>
