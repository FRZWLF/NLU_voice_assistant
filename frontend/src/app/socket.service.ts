import { Injectable } from '@angular/core';
import { Socket } from 'ngx-socket-io';
import {Observable} from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SocketService {
  constructor(private socket: Socket) {
    console.log('Socket.IO Client wird gestartet...');

    this.socket.ioSocket.on('connect', () => {
      console.log('✅ Socket.IO Verbindung erfolgreich hergestellt!');
    });

    this.socket.ioSocket.on('connect_error', (error: any) => {
      console.error('❌ Socket.IO Verbindungsfehler:', error);
    });

    this.socket.ioSocket.on('disconnect', () => {
      console.warn('❗ Socket.IO Verbindung getrennt!');
    });

    this.socket.ioSocket.on('reconnect_attempt', () => {
      console.log('🔄 Versuche, die Socket.IO Verbindung wiederherzustellen...');
    });
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
}
