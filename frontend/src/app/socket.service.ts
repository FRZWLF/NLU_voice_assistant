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

  listenForStreamStatus(): Observable<any> {
    return this.socket.fromEvent('stream_status');
  }
}
