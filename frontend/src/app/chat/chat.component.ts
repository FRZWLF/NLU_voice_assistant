import {Component, OnInit} from '@angular/core';
import { ChatService } from '../chat.service';
import { SocketService } from '../socket.service';


@Component({
  selector: 'app-chat',
  standalone: false,
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  userMessage: string = '';
  streamStatus: any = null;
  messages: { sender: string; text: string }[] = [];
  wifilist: { ssid: string }[] = [];
  selectedSSID: string = '';
  wifiPassword: string = '';
  connectionFeedback: string = '';
  status: string = 'ready';
  musicstate: string = "stop";
  lastPlayedUrl: string | undefined;
  publicKeyPem: string = '';
  shellyDevices: { ssid: string }[] = [];
  selectedDevice: string = '';
  feedbackMessages: string[] = [];

  constructor(private chatService: ChatService, private socketService: SocketService) {}

  sendMessage() {
    if (this.userMessage.trim()) {
      this.messages.push({ sender: 'User', text: this.userMessage });
      // Senden der Nachricht über den Socket
      this.socketService.sendMessage('chat_message', this.userMessage);
      this.chatService.sendMessage(this.userMessage).subscribe((responses: { text: string }[]) => {
        responses.forEach((response: { text: string }) => {
          this.messages.push({ sender: 'Bot', text: response.text });
        });
      });
      this.userMessage = '';
    }
  }

  // Fügt eine Feedback-Nachricht hinzu und entfernt sie nach 5 Sekunden
  addMessage(message: string) {
    this.feedbackMessages.push(message);
  }

  startScan() {
    this.socketService.scanForShellyAP().subscribe((devices) => {
      if (devices.length > 0) {
        this.shellyDevices = devices;
        console.log('Gefundene Shelly-Geräte:', this.shellyDevices);
      } else {
        console.warn('Keine Shelly-Geräte gefunden.');
        this.shellyDevices = [];
      }
    });
  }

  connectToDevice(ssid: string) {
    this.selectedDevice = ssid;
    console.log(`Verbinde mit Access Point: ${ssid}`);

    this.socketService.connectToShellyAP(ssid).subscribe((response) => {
      if (response.status === 'success') {
        console.log('Shelly erfolgreich konfiguriert!');
      } else {
        console.warn(`Fehler: ${response.message}`);
      }
    });
  }

  scanWifi() {
    this.socketService.scanWifi();
  }

  async connectWifi(ssid: string, password: string) {
    try {
      if (!this.publicKeyPem) {
        console.error('Öffentlicher Schlüssel ist nicht verfügbar. Der Schlüsselaustausch wurde nicht durchgeführt.');
        return;
      }

      // WLAN-Daten verschlüsseln und senden
      await this.socketService.sendEncryptedWifiCredentials(ssid, password, this.publicKeyPem);
      console.log('WLAN-Daten erfolgreich verschlüsselt und gesendet.');
    } catch (err) {
      console.error('Fehler bei der Verschlüsselung oder Übertragung der WLAN-Daten:', err);
    }
  }

  stopMusic() {
    // Senden der Nachricht über den Socket
    this.musicstate = "stop"
    this.socketService.stateMusic('music_state', this.musicstate, this.lastPlayedUrl);
  }
  playMusic() {
    // Senden der Nachricht über den Socket
    this.musicstate = "play"
    this.socketService.stateMusic('music_state', this.musicstate, this.lastPlayedUrl);
  }

  async ngOnInit() {
    console.log('ngOnInit der ChatComponent wurde aufgerufen');
    this.socketService.off('ap_connection_result'); // Entfernt alle alten Listener

    // Lausche auf Wake Word Status
    this.socketService.onMessage<any>('wake_word_detected').subscribe((data) => {
      console.log('Wake Word Event empfangen:', data);
      console.log('Komplette Datenstruktur:', JSON.stringify(data));
      this.status = data.status;
    });

    // Lausche auf Chat-Nachrichten
    this.socketService.onMessage<{ sender: string; text: string }>('chat_response').subscribe((message) => {
      console.log('Bot-Nachricht empfangen:', message);
      this.messages.push({ sender: message.sender, text: message.text });
    });

    // Lausche auf Stream-Status-Änderungen
    this.socketService.listenForStreamStatus().subscribe((data) => {
      console.log('Stream-Status erhalten:', data);
      this.streamStatus = data;
      if (data.status === "playing" && data.url) {
        this.lastPlayedUrl = data.url; // Speichere die URL aus dem Backend
      }
    });

    try {
      // RSA-Schlüsselaustausch initialisieren
      this.publicKeyPem = await this.socketService.fetchPublicKey();
      console.log('Public Key empfangen:', this.publicKeyPem);
    } catch (err) {
      console.error('Fehler beim Abrufen des öffentlichen Schlüssels:', err);
    }

    this.scanWifi();
    this.startScan();

    // Lausche auf WLAN-Scan-Ergebnisse
    this.socketService.listenForWifiScan().subscribe((result) => {
      console.log("Empfangene WLAN-Daten:", result);
      if (result.networks) {
        this.wifilist = result.networks.map((ssid: string) => {
          return { ssid };
        });
      } else {
        console.warn("Keine Netzwerke gefunden.");
        this.wifilist = [];
      }
    });

    // Feedback für erfolgreiche Verbindung
    this.socketService.listenForWifiFeedback().subscribe((data) => {
      console.log("WLAN-Verbindung erfolgreich:", data);
      this.connectionFeedback = "Verbindung erfolgreich hergestellt.";
    });

    // Fehler-Feedback
    this.socketService.listenForWifiError().subscribe((error) => {
      console.log("WLAN-Verbindung fehlgeschlagen:", error);
      this.connectionFeedback = "Verbindung fehlgeschlagen.";
    });

    // Lausche auf Shelly-AP-Verbindungsergebnisse
    this.socketService.onMessage<{ status: string; message: string }>('ap_connection_result').subscribe((response) => {
      if (response.status === "success") {
        this.addMessage(`Erfolg: ${response.message}`);
      } else {
        this.addMessage(`Fehler: ${response.message}`);
      }
    });
  }
}
