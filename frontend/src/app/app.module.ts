import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { AppComponent } from './app.component';
import {HttpClientModule} from '@angular/common/http';
import {SocketIoConfig, SocketIoModule} from 'ngx-socket-io';
import {AppRoutingModule} from './app.routing.module';
import {ChatModule} from './chat/chat.module';

// Konfiguration des SocketIo-Servers
const socketConfig: SocketIoConfig = {
  url: 'http://127.0.0.1:5000', // Passe die URL deines Backend-Servers an
  options: {}
};

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    SocketIoModule.forRoot(socketConfig),
    ChatModule
  ],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
