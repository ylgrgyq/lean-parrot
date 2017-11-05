(ns lean-parrot.command.conversation
  (:require [lean-parrot.util :as u]))

(defn conversation-start[m attr transient unique master-key]
  (let [msg {:cmd "conv" :op "start" :i (u/uuid) :m m :attr attr
             :transient transient :unique unique}]
    (u/wrap-with-signature msg aid pid master-key)))

