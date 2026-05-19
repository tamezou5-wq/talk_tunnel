import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg  # 画像を読み込むための道具
import time
import os  # ファイルが存在するか確認するための道具

# --- アプリ設定 ---
st.set_page_config(page_title="トーク・トンネル", layout="centered")

# カスタムCSSで少しおしゃれに（フォントなど）
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #22d3ee; color: black; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚇 トーク・トンネル")
st.write("〜あなたの会話が届かないのは、物理のせいです〜")

# --- 入力セクション：人間関係のパラメータ化 ---
st.sidebar.header("📝 コミュニケーション状況入力")

st.sidebar.subheader("相手のガード (V0)")
q_boss = st.sidebar.toggle("相手は目上の人（上司・先生など）？")
q_mood = st.sidebar.toggle("相手は今、忙しそう or 不機嫌そう？")
q_past = st.sidebar.toggle("過去に既読スルーや塩対応された？")
q_interest = st.sidebar.toggle("相手はこちらに無関心そうだ？") # 追加
q_strict = st.sidebar.toggle("相手は論理的で厳しいタイプだ？") # 追加

# ロジック計算（基本5 + 加算）
v0_base = 5.0 + (5.0 if q_boss else 0) + (10.0 if q_mood else 0) + \
          (5.0 if q_past else 0) + (5.0 if q_interest else 0) + (5.0 if q_strict else 0)
          
st.sidebar.subheader("心の距離 (L)")
q_first = st.sidebar.toggle("初対面、あるいは疎遠である？")
q_distance = st.sidebar.toggle("リモートや物理的に距離がある？")
q_group = st.sidebar.toggle("相手の周りに他の人が大勢いる？") # 追加
q_private = st.sidebar.toggle("かなり踏み込んだ内容の話だ？") # 追加
q_unknown = st.sidebar.toggle("相手の趣味や性格をまだ知らない？") # 追加

# ロジック計算（基本0.5 + 加算）
l_base = 0.5 + (1.0 if q_first else 0) + (0.5 if q_distance else 0) + \
         (0.5 if q_group else 0) + (1.0 if q_private else 0) + (0.5 if q_unknown else 0)

st.sidebar.subheader("あなたの突破力 (E)")
q_conf = st.sidebar.toggle("そのネタに絶対の自信がある！")
q_alcohol = st.sidebar.toggle("お酒やカフェインの勢いがある！")
q_prep = st.sidebar.toggle("話す内容を事前にシミュレーションした？") # 追加
q_benefit = st.sidebar.toggle("相手にとっても得な話である？") # 追加
q_passion = st.sidebar.toggle("とにかく伝えたい情熱がある！") # 追加

# ロジック計算（基本5 + 加算）
e_base = 5.0 + (8.0 if q_conf else 0) + (5.0 if q_alcohol else 0) + \
         (5.0 if q_prep else 0) + (7.0 if q_benefit else 0) + (5.0 if q_passion else 0)

# 4. ノイズ (T)
st.sidebar.subheader("環境ノイズ")
q_noise = st.sidebar.select_slider("周囲のガヤガヤ度", options=["静寂", "普通", "賑やか", "爆音"])
noise_map = {"静寂": 0.1, "普通": 1.0, "賑やか": 2.5, "爆音": 5.0}
t_noise = noise_map[q_noise]

# --- 物理計算（透過確率 T） ---
def get_transmission_prob(E, V0, L):
    if E > V0:
        k_wall = np.sqrt(E - V0 + 1e-9)
        T = 1 / (1 + (V0**2 * (np.sin(k_wall * L))**2) / (4 * E * (E - V0 + 1e-9)))
    else:
        kappa = np.sqrt(V0 - E + 1e-9)
        T = 1 / (1 + (V0**2 * (np.sinh(kappa * L))**2) / (4 * E * (V0 - E + 1e-9)))
    return float(np.clip(T, 0, 1))

prob = get_transmission_prob(e_base, v0_base, l_base)



@st.cache_data
def get_base_bg():
    return mpimg.imread("talk_tunnel.jpg")

bg_img = get_base_bg()

# --- アニメーション実行セクション ---
st.write("---")
if st.button("🚀 物理演算で会話を送信する"):
    
    # アニメーション用のプレースホルダー
    plot_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # X軸の定義
    x = np.linspace(0, 10, 300)
    barrier_start = 4.0
    barrier_end = barrier_start + l_base
    
    # アニメーションループ
    steps = 25 # 反射波を見るためにステップ数を少し増やします
    
    plot_placeholder = st.empty() # 描画専用の「窓」を固定
    
    for i in range(steps):
        t = i / steps * 14  # 波の中心位置（壁を越えて少し進むまで）
            
        # --- プロット設定 (画像のようなダークモード風) ---
        # facecolor='#000000' で背景を黒に
        # fig自体の背景を黒にする（これはそのままでOK）
        # 1. グラフ全体の背景を透明にする
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='none') 
        
        # 2. 描画エリア（プロット部分）の背景も透明にする
        ax.patch.set_alpha(0) 
        
        # 3. 背景画像を一番下に描画（zorderをマイナスにすると確実です）
        ax.imshow(bg_img, extent=[0, 10, -1.5, 1.5], aspect='auto', alpha=0.8, zorder=-1)
            
        # 壁の描画 (zorder=1)
        ax.axvspan(barrier_start, barrier_end, color='#f97316', alpha=0.6, zorder=1)
            
        # 2. 波束の基本生成 (ガウス波束)
        y_base = np.exp(-(x - t)**2 / 0.5) * np.sin(2 * np.pi * 2 * x)
            
        # --- 物理描画：透過、反射、減衰 ---
        # A. 透過波 (壁より後ろ)
        y_trans = np.where(x > barrier_end, y_base * np.sqrt(prob), 0)
            
        # B. 減衰波 (壁の中)
        mask = (x >= barrier_start) & (x <= barrier_end)
        num_in_wall = np.sum(mask)
        y_wall = np.zeros_like(x)
        if num_in_wall > 0:
            decay = np.linspace(1.0, np.sqrt(prob), num_in_wall)
            # 壁の中にある波の「入り口から出口まで」だけを取り出して減衰させる
            y_wall[mask] = y_base[mask] * decay

        # C. 入射波 (壁の手前)
        # まだ壁に達していない波だけを描画
        y_inc = np.where(x < barrier_start, y_base, 0)

        # D. 反射波 (壁の手前) --- 【追加機能】 ---
        # 反射波は「自分の方へ戻ってくる」ので、位置を逆に計算する
        # また、反射率 (1 - prob) に応じて振幅を変える
        t_ref = barrier_start - (t - barrier_start) # 壁を原点とした折り返し
        y_ref_base = np.exp(-(x - t_ref)**2 / 0.5) * np.sin(2 * np.pi * 2 * x)
        # 壁にぶつかった後だけ、かつ自分の方へ戻る波だけ、振幅を調整して描画
        y_ref = np.where((x < barrier_start) & (t > barrier_start), y_ref_base * np.sqrt(1 - prob), 0)
            
        # --- 全体の波の合成 ---
        # ノイズ(t_noise)の影響もここで簡易的に加える（振幅のゆらぎ）
        noise_factor = 1.0 + (np.random.rand(len(x)) - 0.5) * t_noise * 0.05
        y_final = (y_inc + y_trans + y_wall + y_ref) * noise_factor

        # 3. 波の描画
        # 透過波と減衰波はシアン(#22d3ee)
        ax.plot(x, y_trans + y_wall, color='#22d3ee', lw=3)
        # 入射波は少し薄く
        ax.plot(x, y_inc, color='#22d3ee', lw=3, alpha=0.6)
        # 反射波は黄色(#fbbf24)で表現 --- 【追加機能】 ---
        ax.plot(x, y_ref, color='#fbbf24', lw=2, linestyle='--', alpha=0.8)
            
        # 4. 描画設定のブラッシュアップ
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlim(0, 10)
        ax.axis('off') # 軸を消して「絵」にする

        # 5. キャラクターとテキストの配置 --- 【追加機能】 ---
        # Matplotlibのtext関数で絵文字を配置する（スマホでも見れる）
        # ha='center', va='center' で中心を合わせる
        ax.text(1.5, 1.2, "YOU", color="white", fontsize=16, ha='center', va='center', fontweight='bold')
        ax.text(8.5, 1.2, "RECIPIENT", color="white", fontsize=16, ha='center', va='center', fontweight='bold')
            
        # 物理パラメータのラベル追加
        ax.text(0.5, -1.2, f"E:{e_base:.1f}", color="#22d3ee", fontsize=10, ha='center')
        ax.text(barrier_start + l_base/2, -1.2, f"V0:{v0_base:.1f}\nL:{l_base:.1f}", color="#f97316", fontsize=10, ha='center')

        plot_placeholder.pyplot(fig, transparent=True)
        plt.close(fig)
        #time.sleep(0.01) # 描画速度の調整
        
    # --- 最終結果の表示 ---
    st.subheader(f"解析結果：透過確率（成功率） {prob:.2%}")
    # 上記のif-elif文で決まったmsgを表示
  
    # 透過確率 prob に基づくメッセージ分岐
    if prob == 0:
        msg = "【全反射】物理法則があなたの接触を拒絶しています。存在確率がゼロです。今日は波動関数を閉じて寝ましょう。"
    elif prob < 0.05:
        msg = "【観測失敗】量子トンネル効果の兆しすらありません。ポテンシャル障壁が高すぎます。まずは雑談でV0を下げてください。"
    elif prob < 0.15:
        msg = "【極微弱透過】奇跡的なトンネル効果で1語だけ染み出しましたが、相手は『空耳かな？』と思っています。位相を整えて再送してください。"
    elif prob < 0.30:
        msg = "【不確定性優位】伝わっているかいないか、シュレディンガーの猫状態です。相手の反応を観測するまで結果は確定しません。"
    elif prob < 0.45:
        msg = "【部分透過】波動の半分が右から左へ受け流されました。エネルギー不足です。もう少しネタの振幅（熱量）を大きくしましょう。"
    elif prob < 0.60:
        msg = "【共鳴不完全】通信成立。ただし波形が乱れています。ノイズ（周囲の目）を減らすか、コヒーレンス（話の一貫性）を高めてください。"
    elif prob < 0.75:
        msg = "【安定通信】干渉成功！あなたの波動関数は相手の心と良好に重なっています。このまま定常波を維持しましょう。"
    elif prob < 0.85:
        msg = "【高確率透過】ほぼ完璧に届いています。相手の心というポテンシャルの中に、あなたの言葉が完全に染み渡りました。"
    elif prob < 0.95:
        msg = "【完全透過】障壁を無視して直撃しています。もはや壁はありません。ここからは物理ではなく心理学の領域です。"
    else:
        msg = "【オーバーフロー】エネルギー過剰です！勢いが強すぎて相手のポテンシャルが崩壊する恐れがあります。出力を絞ってください。"

    # 物理学的な一言（ランダムにしても面白い）
    #st.info(f"💡 物理学的アドバイス：壁の厚さ(L)が{l_base:.1f}と観測されました。初対面の不確定性を下げるため、まずは観測（挨拶）を繰り返してください。")

    # 上記のif-elif文で決まったmsgを表示
    st.info(f"🔬 **物理学的診断：** \n\n {msg}")
    
    advices = []

    # 1. 相手のガード (V0) が高い場合
    if v0_base > e_base:
        advices.append(f"相手のポテンシャル障壁(V0={v0_base:.1f})が、あなたのエネルギー(E={e_base:.1f})を上回っています。まずは世間話で『心の導電率』を高め、V0を中和してください。")

    # 2. 壁の厚さ (L) が厚い場合
    if l_base > 2.0:
        advices.append(f"心の壁の厚さ(L={l_base:.1f})が広範囲に及んでいます。量子トンネル効果を狙うには、接触回数（観測）を増やし、波束の収束を待つのが定石です。")

    # 3. 自分のエネルギー (E) が低い場合
    if e_base < 10.0:
        advices.append(f"基底状態(E={e_base:.1f})に近いエネルギーレベルです。自信（振幅）を増幅させるか、アルコール等の外部エネルギーを注入して励起状態に移行してください。")

    # 4. 全反射条件に近い場合
    if v0_base > 25.0:
        advices.append("強固な絶縁体状態です。今の位相で突撃しても全反射されるだけです。一度自由空間に身を置き、波動関数を再構築して出直してください。")

    # 5. 透過確率が高い場合（成功時）
    if prob > 0.8:
        advices.append(f"完全に共鳴しています！壁の厚さ(L)を無視できるほどの波長でアプローチできています。今のコヒーレンス（一貫性）を保ったまま送信を完了してください。")

    # 該当するアドバイスからランダム、または複数表示
    import random
    if advices:
        selected_advice = random.choice(advices)
    else:
        selected_advice = "定常状態です。特に物理的な異常は見当たりません。そのままのあなたで送信してください。"

    st.info(f"💡 **物理学的アドバイス：**\n\n{selected_advice}")
        
else:
    st.info("左側のパラメータを設定して「解析開始」を押してください。")