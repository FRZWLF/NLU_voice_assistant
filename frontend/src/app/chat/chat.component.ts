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
  messages: { sender: string; text: string }[] = [];
  status: string = 'ready'

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

  ngOnInit() {
    console.log('ngOnInit der ChatComponent wurde aufgerufen');

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
  }
}
