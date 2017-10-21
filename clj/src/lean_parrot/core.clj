(ns lean-parrot.core
  (:require [lean-parrot.connection :as conn])
  (:import (io.netty.handler.codec.http.websocketx CloseWebSocketFrame)
           (io.netty.channel ChannelFuture)))





(defn connect[run-after-connect]
  (let [chf (conn/connect)]
    (.awaitUninterruptibly chf 10000)
    (if (.isSuccess ^ChannelFuture chf)
      (println "connect successful!")
      (throw (Exception. "connect failed")))))



