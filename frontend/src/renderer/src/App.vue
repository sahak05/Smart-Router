<template>
  <v-app>
    <v-app-bar color="surface-variant" elevation="2">
      <v-app-bar-title>Smart Router Admin</v-app-bar-title>
      <template v-slot:append>
        <v-btn icon="mdi-shield-check"></v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <v-container>
        <v-card class="pa-5 mt-5">
          <v-card-title class="text-h5">Dashboard Initialization</v-card-title>
          <v-card-text>
            If this card is dark grey and the button below looks like a modern Material button, Vuetify is successfully installed!
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" variant="elevated" prepend-icon="mdi-rocket">
              System Ready
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
</script>
