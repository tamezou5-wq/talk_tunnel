import streamlit as st
import numpy as np
import streamlit.components.v1 as components
import base64
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


# 関係性の選択肢リスト（最初に「選択してください」を入れる）
rel_options = ["選択してください", "先輩後輩", "友人", "恋人", "他人", "家族"]

relationship = st.sidebar.selectbox("相手との関係は？", rel_options)

# 解析ボタンの直前や、解析の開始地点でチェックする
if relationship == "選択してください":
    st.warning("まずはサイドバーから『相手との関係』を選択してください！")
    # ここで処理を止める（以後の計算コードをスキップさせる）
    st.stop()

st.sidebar.subheader("相手のガード (V0)")
q_boss = st.sidebar.toggle("話しかけるのに気を遣う")
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

def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 画像がカレントディレクトリにある前提
try:
    img_base64 = get_image_base64("talk_tunnel.jpg")
except:
    st.error("背景画像 'talk_tunnel.jpg' が見つかりません。")
    img_base64 = ""

def render_p5_animation(E, V0, L, prob, img_data):
    # f-stringの中で { } を文字として扱うために {{ }} に書き換えます
    p5_code = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.js"></script>
    <div id="p5-container" style="display: flex; justify-content: center;"></div>
    <script>
    let bg;
    let t = -2.0; 
    let isAnimating = true;

    function preload() {{
        bg = loadImage('data:image/jpeg;base64,{img_data}');
    }}

    function setup() {{
        let containerWidth = document.getElementById('p5-container').offsetWidth;
        let canvas = createCanvas(containerWidth, containerWidth * (320/800));
        canvas.parent('p5-container');
        frameRate(60);
    }}

    function draw() {{
        if (!isAnimating) return;

        image(bg, 0, 0, width, height);
        
        let center_x_norm = 5.0; 
        let bWidth_norm = {L}; 
        let bStart_norm = center_x_norm - bWidth_norm / 2; 
        let bEnd_norm = center_x_norm + bWidth_norm / 2; 

        let bStart_px = map(bStart_norm, 0, 10, 0, width);
        let bEnd_px = map(bEnd_norm, 0, 10, 0, width);
        let bWidth_px = bEnd_px - bStart_px;
        
        noStroke();
        fill(249, 115, 22, 120); 
        rect(bStart_px, height * 0.15, bWidth_px, height * 0.7); 

        fill(255);
        textAlign(CENTER);
        textSize(width / 50);
        text("YOU", width * 0.15, height * 0.1);
        text("RECIPIENT", width * 0.85, height * 0.1);

        noFill();
        strokeWeight(3);
        stroke(34, 211, 238); 
        
        beginShape();
        for (let x = 0; x < width; x++) {{
            let x_norm = map(x, 0, width, 0, 10);
            let wave = exp(-pow(x_norm - t, 2) / 0.5) * sin(2 * PI * 2 * x_norm);
            let y = 0;

            if (x_norm < bStart_norm) {{
                y = wave * 60;
            }} else if (x_norm >= bStart_norm && x_norm <= bEnd_norm) {{
                let d = map(x_norm, bStart_norm, bEnd_norm, 1.0, sqrt({prob}));
                y = wave * 60 * d;
            }} else {{
                y = wave * 60 * sqrt({prob});
            }}
            vertex(x, height / 2 + y);
        }}
        endShape();

        stroke(251, 191, 36, 150); 
        strokeWeight(2);
        beginShape();
        if (t > bStart_norm) {{
            let t_ref = bStart_norm - (t - bStart_norm);
            for (let x = 0; x < bStart_px; x++) {{
                let x_norm = map(x, 0, width, 0, 10);
                let ref_wave = exp(-pow(x_norm - t_ref, 2) / 0.5) * sin(2 * PI * 2 * x_norm);
                vertex(x, height / 2 + ref_wave * 40 * sqrt(1 - {prob}));
            }}
        }}
        endShape();

        t += 0.05;
        if (t > 12.0) isAnimating = false;
    }}
    </script>
    """
    components.html(p5_code, height=280)

# --- アニメーション実行セクション ---
st.write("---")
if st.button("🚀 物理演算で会話を送信する"):
 
    render_p5_animation(e_base, v0_base, l_base, prob, img_base64)
    
    
    # 2. 結果を表示するための「空のコンテナ」を準備
    result_container = st.empty()
    
    # 3. 波が移動しきるまで待機
    # t += 0.06 の場合、t=12.0 に達するまで約4〜5秒ほどです
    # （PCのスペックによりますが、実測で微調整してください）
    import time
    time.sleep(4.5)
    
    with result_container.container():
    # --- 最終結果の表示 （以下、元のコードのまま）---
        st.subheader(f"解析結果：透過確率（成功率） {prob:.2%}")
    # 上記のif-elif文で決まったmsgを表示
    
        # 物理学的相性診断の辞書
        
        if relationship == "先輩後輩" and prob > 0.5:
            msg_re = "【マクスウェル方程式型】電場と磁場のように、直交しながら支え合って進んでいくプロフェッショナルな関係。"
        if relationship == "友人" and prob > 0.5:
            msg_re = "【LC回路共鳴型】周波数が一致した瞬間にエネルギーが最大化する、心地よい振動ペア。"
        if relationship == "恋人" and prob > 0.5:
            msg_re = "【量子もつれ型】距離や時間を超えて同期する、不気味な遠隔作用が働いている運命共同体。"
        if relationship == "他人" and prob > 0.5:
             msg_re = "【不確定型（ハイゼンベルク）】観測するまで状態が定まらない、スリリングな未知のポテンシャル。"       
        if relationship == "家族" and prob > 0.5:
             msg_re = "【強結合型】エネルギー準位が強固に結びつき、分離不可能なほど安定した系。"
        
        if relationship == "先輩後輩" and prob <= 0.5:
            msg_re = "【誘電分極未達型】電場と磁場のように、まだ相手のポテンシャルを分極させるだけの電圧が足りていません。"
        if relationship == "友人" and prob <= 0.5:
            msg_re = "【同調不全型】お互いの周波数がズレていて、打ち消し合っています。"
        if relationship == "恋人" and prob <= 0.5:
            msg_re = "【デコヒーレンス型】環境ノイズ（周囲の目）が強すぎて、せっかくの量子もつれ状態が解けてしまいました。"
        if relationship == "他人" and prob <= 0.5:
             msg_re = "【非相互作用型】まだお互いの波動関数が重なり合っていません。"
        if relationship == "家族" and prob <= 0.5:
             msg_re = "【エネルギー準位不整合型】家族なのに基底状態のエネルギーレベルが噛み合っていません。"
        

        # 診断結果の表示に混ぜる
        st.info(f"🙏 **物理学的相性：** \n\n {msg_re}")

    
  
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
        if t_noise > 2.0:
            advices.append(f"周囲のノイズが波動関数を無作為に収束させています。相手の心というポテンシャルを観測するためには、S/N比を向上させる『静寂』というフィルタリングが不可欠です。")

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


        import random
        # 該当するアドバイスからランダム、または複数表示
        if advices:
            # リストから最大2つをランダムに抽出（リストが1つしかない場合は1つだけ抽出）
            k = min(len(advices), 2)
            selected_advices = random.sample(advices, k)
            
            # リストの各要素を「・」付きの箇条書きにして結合
            formatted_advice = "\n\n".join([f"・{adv}" for adv in selected_advices])
            st.info(f"💡 **物理学的アドバイス：**\n\n{formatted_advice}")
        else:
            st.info("💡 **物理学的アドバイス：**\n\n定常状態です。特に物理的な異常は見当たりません。そのままのあなたで送信してください。")

        st.divider() # 区切り線を入れて視覚的に分ける
        st.caption("※物理的アプローチによる診断結果です。不確定性原理により、結果は常に変動します。今日と明日で診断が変わるのも、量子力学的には正しい挙動です。")
        
        
else:
    st.info("左側のパラメータを設定して「解析開始」を押してください。")