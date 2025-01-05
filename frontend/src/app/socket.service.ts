import { Injectable } from '@angular/core';
import { Socket } from 'ngx-socket-io';
import {Observable} from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SocketService {
  constructor(private socket: Socket) {
    console.log('Socket.IO Client wird gestartet...');

    console.log('Socket.IO Verbindung wird gestartet...');
    this.socket.on('connect', () => console.log('✅ Verbindung hergestellt'));
    this.socket.on('disconnect', () => console.warn('❗ Verbindung getrennt'));
  }

  // Lausche auf ein bestimmtes Event
  onMessage<T>(event: string): Observable<T> {
    console.log(`Lausche auf Event: ${event}`);
    return this.socket.fromEvent<T>(event);
  }

  // Sende eine Nachricht an den Server
  sendMessage(event: string, message: any) {
    console.log(`Sende Nachricht: Event - ${event}, Message - ${message}`);
    this.socket.emit(event, message);
  }

  // WLAN-Scan anfordern
  scanWifi() {
    console.log("Starte WLAN-Scan...");
    this.socket.emit('scan_wifi');
  }

  async fetchPublicKey(): Promise<string> {
    try {
      const response = await fetch('http://localhost:5000/get-public-key'); // API-URL anpassen
      const data = await response.json();
      return data.public_key;
    } catch (error) {
      console.error("Fehler beim Abrufen des öffentlichen Schlüssels:", error);
      throw error;
    }
  }

  async encryptAESKeyWithRSA(aesKey: Uint8Array, publicKeyPem: string): Promise<string> {
    console.log('Empfangener Public Key:', publicKeyPem);

    // Konvertiere den PEM-String in ArrayBuffer
    const publicKeyArrayBuffer = this.str2ab(publicKeyPem);

    const publicKey = await crypto.subtle.importKey(
      'spki',
      publicKeyArrayBuffer,
      { name: 'RSA-OAEP', hash: 'SHA-256' },
      false,
      ['encrypt']
    );
    console.log('Public Key erfolgreich importiert:', publicKey);

    // Verschlüssele den AES-Schlüssel mit RSA
    const encryptedKey = await crypto.subtle.encrypt(
      { name: 'RSA-OAEP' },
      publicKey,
      aesKey
    );
    console.log('AES-Schlüssel erfolgreich mit RSA verschlüsselt:', encryptedKey);

    return this.arrayBufferToBase64(encryptedKey);
  }

  // WLAN-Daten mit AES verschlüsseln
  async encryptWifiCredentials(ssid: string, password: string, aesKey: Uint8Array): Promise<{ iv: string; ciphertext: string; tag: string }> {
    console.log('Verwendeter AES-Schlüssel:', aesKey);

    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      aesKey,
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    );
    console.log('AES-Schlüssel erfolgreich importiert:', cryptoKey);

    const iv = crypto.getRandomValues(new Uint8Array(12));
    console.log('Generierte IV:', iv);

    const encodedData = new TextEncoder().encode(JSON.stringify({ ssid, password }));
    console.log('Zu verschlüsselnde Daten:', encodedData);

    const encryptResult = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      encodedData
    );
    console.log('Daten erfolgreich verschlüsselt:', encryptResult);

    const ciphertext = new Uint8Array(encryptResult);
    const tag = ciphertext.slice(-16);

    return {
      iv: this.arrayBufferToBase64(iv),
      ciphertext: this.arrayBufferToBase64(ciphertext.slice(0, -16)),
      tag: this.arrayBufferToBase64(tag)
    };
  }

  // Sende verschlüsselte WLAN-Daten an den Server
  async sendEncryptedWifiCredentials(ssid: string, password: string, publicKeyPem: string) {
    const aesKey = crypto.getRandomValues(new Uint8Array(32)); // Generiere AES-Schlüssel
    const encryptedAESKey = await this.encryptAESKeyWithRSA(aesKey, publicKeyPem);

    const encryptedData = await this.encryptWifiCredentials(ssid, password, aesKey);

    this.socket.emit('save_wifi_credentials', {
      encrypted_key: encryptedAESKey,
      iv: encryptedData.iv,
      ciphertext: encryptedData.ciphertext,
      tag: encryptedData.tag
    });
  }

  // Lausche auf WLAN-Scan-Ergebnisse
  listenForWifiScan(): Observable<any> {
    return this.socket.fromEvent('wifi_networks');
  }

  // Lausche auf Feedback zur WLAN-Verbindung
  listenForWifiFeedback(): Observable<any> {
    return this.socket.fromEvent('wifi_save_success');
  }

  listenForWifiError(): Observable<any> {
    return this.socket.fromEvent('wifi_save_error');
  }

  // Sende eine Nachricht an den Server
  stateMusic(event: string, state: string, url?: string) {
    console.log(`Sende Nachricht: Event - ${event}, State - ${state}, URL - ${url}`);
    this.socket.emit(event, { state, url });
  }

  listenForStreamStatus(): Observable<any> {
    return this.socket.fromEvent('stream_status');
  }

  scanForShellyAP(): Observable<{ ssid: string }[]> {
    this.socket.emit('shelly_ap_scan');
    return this.socket.fromEvent<{ ssid: string }[]>('ap_scan_result');
  }

  connectToShellyAP(ssid: string): Observable<{ status: string; message: string }> {
    this.socket.emit('connect_shelly_ap', { ssid });
    return this.socket.fromEvent<{ status: string; message: string }>('ap_connection_result');
  }


  // Hilfsfunktion: ArrayBuffer in Base64 umwandeln
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private str2ab(pem: string): ArrayBuffer {
    console.log('Konvertiere PEM in ArrayBuffer...');

    // Entferne die Header und Footer des PEM-Schlüssels
    const pemHeader = "-----BEGIN PUBLIC KEY-----";
    const pemFooter = "-----END PUBLIC KEY-----";
    const pemContents = pem.replace(pemHeader, "").replace(pemFooter, "").replace(/\s+/g, "");

    // Dekodiere Base64 und konvertiere in einen ArrayBuffer
    const binaryDerString = atob(pemContents);
    const binaryDer = new Uint8Array(binaryDerString.length);
    for (let i = 0; i < binaryDerString.length; i++) {
      binaryDer[i] = binaryDerString.charCodeAt(i);
    }

    console.log('Konvertierung abgeschlossen:', binaryDer);
    return binaryDer.buffer;
  }

  off(event: string) {
    this.socket.removeAllListeners(event);
  }
}
