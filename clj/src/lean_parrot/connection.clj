(ns lean-parrot.connection
  (:require [clojure.data.json :as json]
            [clojure.tools.logging :as log]
            [clojure.stacktrace :refer [print-stack-trace]]
            [lean-parrot.router :as router]
            [lean-parrot.config :as config])
  (:import (io.netty.handler.codec.http HttpObjectAggregator HttpClientCodec DefaultHttpHeaders)
           (io.netty.channel Channel ChannelInitializer SimpleChannelInboundHandler ChannelHandlerContext
                             ChannelFuture ChannelHandler ChannelPromise)
           (io.netty.handler.codec.http.websocketx WebSocketVersion WebSocketClientProtocolHandler
                                                   TextWebSocketFrame PingWebSocketFrame
                                                   WebSocketClientProtocolHandler$ClientHandshakeStateEvent CloseWebSocketFrame)
           (java.net URI InetSocketAddress)
           (io.netty.channel.nio NioEventLoopGroup)
           (io.netty.bootstrap Bootstrap)
           (io.netty.channel.socket.nio NioSocketChannel)
           (io.netty.handler.timeout IdleStateHandler IdleStateEvent)
           (java.util.concurrent TimeUnit ScheduledFuture)
           (io.netty.util.concurrent GenericFutureListener FailedFuture GlobalEventExecutor Future)))

(def ^:private connection-promise (atom nil))
(defonce ^:priavate reconnect-future (atom nil))
(defonce ^:priavate connecting-lock (Object.))
(defonce ^:private i->call-back (atom {}))

(defn ^Future send! [msg]
  (if-let [promise @connection-promise]
    (let [^Channel ch (.channel promise)]
      (log/info "Write:" msg)
      (let [msg (if (map? msg) (->> msg (json/write-str) (TextWebSocketFrame.)) msg)]
        (.writeAndFlush ^Channel ch msg)))
    (FailedFuture. GlobalEventExecutor/INSTANCE (RuntimeException. "Please call connect first"))))

(defn client-ws-handler []
  (proxy [SimpleChannelInboundHandler] []
    (isSharable [] true)

    (exceptionCaught [^ChannelHandlerContext _ ^Throwable e]
      (log/error e "Got exception"))

    (userEventTriggered [^ChannelHandlerContext ctx evt]
      (cond
        (instance? IdleStateEvent evt)
        (let [frame (PingWebSocketFrame.)]
          (.writeAndFlush ctx frame))

        (= evt WebSocketClientProtocolHandler$ClientHandshakeStateEvent/HANDSHAKE_COMPLETE)
        (do
          (log/info "Websocket hand shake complete")
          (.trySuccess ^ChannelPromise @connection-promise))))

    (channelRead0 [^ChannelHandlerContext ctx msg]
      (let [ch# (.channel ctx)]
        (if (instance? TextWebSocketFrame msg)
          (println "Receive from server: " (.text ^TextWebSocketFrame msg))
          (println "Receive" msg))))))

(defn connect [{:keys [uri ping-interval-ms subprotocol reconnect-delay-ms reconnect-times max-reconnect-times]
                :or   {ping-interval-ms    20000
                       reconnect-delay-ms  1000
                       subprotocol         config/default-subprotocol
                       max-reconnect-times 3
                       reconnect-times     0}
                :as   opts}]
  (locking connecting-lock
    (if @connection-promise
      (cast ChannelFuture @connection-promise)
      (let [^URI uri       (if uri uri (router/get-server-uri config/aid))
            channel-init   (proxy [ChannelInitializer] []
                             (initChannel [^Channel ch]
                               (try
                                 (.addLast (.pipeline ch)
                                   (into-array ChannelHandler [(HttpClientCodec.)
                                                               (HttpObjectAggregator. 65535)
                                                               (WebSocketClientProtocolHandler. uri WebSocketVersion/V13 subprotocol false
                                                                 (DefaultHttpHeaders.) 65535 false)
                                                               (IdleStateHandler. 0 0 ping-interval-ms TimeUnit/MILLISECONDS)
                                                               (client-ws-handler)]))
                                 (catch Exception e
                                   (print-stack-trace e)))))
            bootstrap      (doto (Bootstrap.)
                             (.group (NioEventLoopGroup.))
                             (.channel NioSocketChannel)
                             (.handler channel-init))
            _              (log/infof "connecting %s..." uri)
            addr           (InetSocketAddress. (.getHost uri) (.getPort uri))
            connect-future (.connect bootstrap addr)
            close-future   (.closeFuture (.channel connect-future))
            promise        (.newPromise (.channel connect-future))]
        (.addListener close-future (reify GenericFutureListener
                                     (operationComplete [this future]
                                       (log/info "Connection closed" (.cause future))
                                       (when-let [old-conn-promise @connection-promise]
                                         (.tryFailure @connection-promise (IllegalStateException. "Connection closed"))
                                         (locking connecting-lock
                                           (when (compare-and-set! connection-promise old-conn-promise nil)
                                             (let [^ScheduledFuture future
                                                   (.schedule (.eventLoop (.channel future))
                                                     (fn []
                                                       (when (< reconnect-times max-reconnect-times)
                                                         (connect (update opts :reconnect-times inc))))
                                                     reconnect-delay-ms TimeUnit/MILLISECONDS)]
                                               (reset! reconnect-future future))))))))
        (reset! connection-promise promise)
        (cast ChannelFuture promise)))))

(defn disconnect []
  (locking connecting-lock
    (let [conn-promiese @connection-promise]
      (reset! connection-promise nil)
      (when @reconnect-future
        (.cancel @reconnect-future true))
      (send! (CloseWebSocketFrame.))
      (some->> conn-promiese
        (.channel)
        (.close)))))
