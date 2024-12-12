import { Component } from '@angular/core';
import { ChatService } from '../chat.service';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule, HttpClientModule, CommonModule],
  providers: [ChatService],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  userMessage: string = '';
  messages: { sender: string; text: string }[] = [];

  constructor(private chatService: ChatService) {}

  sendMessage() {
    if (this.userMessage.trim()) {
      this.messages.push({ sender: 'User', text: this.userMessage });
      this.chatService.sendMessage(this.userMessage).subscribe((responses: any[]) => {
        responses.forEach((response: { text: string }) => {
          this.messages.push({ sender: 'Bot', text: response.text });
        });
      });
      this.userMessage = '';
    }
  }
}
