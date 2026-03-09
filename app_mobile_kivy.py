from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import correcao_qrcode_simples as core


def show_message(title: str, text: str) -> None:
    content = BoxLayout(orientation="vertical", spacing=8, padding=12)
    content.add_widget(Label(text=text))
    btn = Button(text="OK", size_hint=(1, 0.25))
    popup = Popup(title=title, content=content, size_hint=(0.9, 0.5))
    btn.bind(on_release=popup.dismiss)
    content.add_widget(btn)
    popup.open()


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=14, spacing=10)
        layout.add_widget(Label(text="Sistema de Correcao por QR", size_hint=(1, 0.15)))

        btn1 = Button(text="1) Configurar prova + QR oficial", size_hint=(1, 0.14))
        btn2 = Button(text="2) Gerar gabarito/folha do aluno", size_hint=(1, 0.14))
        btn3 = Button(text="3) Corrigir imagens (pasta resultado)", size_hint=(1, 0.14))
        btn4 = Button(text="4) Ver pasta resultado", size_hint=(1, 0.14))

        btn1.bind(on_release=self.ir_config)
        btn2.bind(on_release=self.ir_folha)
        btn3.bind(on_release=self.ir_correcao)
        btn4.bind(on_release=lambda *_: show_message("Pasta", str(core.PASTA_RESULTADO)))

        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)
        layout.add_widget(btn4)
        self.add_widget(layout)

    def ir_config(self, *_):
        self.manager.current = "config"

    def ir_folha(self, *_):
        self.manager.current = "folha"

    def ir_correcao(self, *_):
        self.manager.current = "correcao"


class ConfigScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        root.add_widget(Label(text="Configurar Prova", size_hint=(1, 0.12)))

        self.prova_id = TextInput(hint_text="ID da prova (ex: AV1)", multiline=False)
        self.qtd = TextInput(hint_text="Qtd questoes (ex: 20)", multiline=False, input_filter="int")
        self.gabarito = TextInput(hint_text="Gabarito (ex: ABCDEABCDE...)", multiline=False)
        self.ponto = TextInput(hint_text="Ponto por questao (ex: 0.5)", multiline=False)

        for w in (self.prova_id, self.qtd, self.gabarito, self.ponto):
            root.add_widget(w)

        row = BoxLayout(size_hint=(1, 0.2), spacing=8)
        btn_salvar = Button(text="Salvar")
        btn_voltar = Button(text="Voltar")
        btn_salvar.bind(on_release=self.salvar)
        btn_voltar.bind(on_release=self.voltar)
        row.add_widget(btn_salvar)
        row.add_widget(btn_voltar)
        root.add_widget(row)
        self.add_widget(root)

    def voltar(self, *_):
        self.manager.current = "home"

    def salvar(self, *_):
        try:
            cfg = core.validar_config(
                {
                    "prova_id": self.prova_id.text.strip() or "PROVA",
                    "qtd_questoes": int(self.qtd.text.strip()),
                    "gabarito": core.normalizar_respostas(self.gabarito.text),
                    "ponto_por_questao": float(self.ponto.text.strip().replace(",", ".")),
                }
            )
            core.salvar_config(cfg)
            qr = core.gerar_qr_oficial(cfg)
            show_message("Sucesso", f"Configuracao salva.\nQR oficial: {qr}")
        except Exception as e:
            show_message("Erro", str(e))


class FolhaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        root.add_widget(Label(text="Gerar Folha do Aluno", size_hint=(1, 0.12)))

        self.aluno = TextInput(hint_text="Aluno ID", multiline=False)
        self.nome = TextInput(hint_text="Nome do aluno", multiline=False)
        root.add_widget(self.aluno)
        root.add_widget(self.nome)

        row = BoxLayout(size_hint=(1, 0.2), spacing=8)
        btn_gerar = Button(text="Gerar")
        btn_voltar = Button(text="Voltar")
        btn_gerar.bind(on_release=self.gerar)
        btn_voltar.bind(on_release=self.voltar)
        row.add_widget(btn_gerar)
        row.add_widget(btn_voltar)
        root.add_widget(row)
        self.add_widget(root)

    def voltar(self, *_):
        self.manager.current = "home"

    def gerar(self, *_):
        try:
            cfg = core.carregar_config()
            aluno_id = self.aluno.text.strip()
            if not aluno_id:
                raise ValueError("Aluno ID obrigatorio.")
            qr = core.gerar_qr_oficial(cfg)
            pdf = core.gerar_folha_aluno_pdf(
                cfg,
                aluno_id=aluno_id,
                nome_aluno=self.nome.text.strip(),
                qr_oficial_path=qr,
                respostas_aluno="",
            )
            show_message("Sucesso", f"QR oficial: {qr}\nFolha: {pdf}")
        except Exception as e:
            show_message("Erro", str(e))


class CorrecaoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        root.add_widget(Label(text="Correcao por imagens", size_hint=(1, 0.12)))
        root.add_widget(Label(text="Use a pasta resultado para as fotos.", size_hint=(1, 0.1)))

        self.nome = TextInput(hint_text="Nome do aluno", multiline=False)
        self.turma = TextInput(hint_text="Turma", multiline=False)
        self.serie = TextInput(hint_text="Serie", multiline=False)
        root.add_widget(self.nome)
        root.add_widget(self.turma)
        root.add_widget(self.serie)

        row = BoxLayout(size_hint=(1, 0.2), spacing=8)
        btn_corrigir = Button(text="Corrigir agora")
        btn_voltar = Button(text="Voltar")
        btn_corrigir.bind(on_release=self.corrigir)
        btn_voltar.bind(on_release=self.voltar)
        row.add_widget(btn_corrigir)
        row.add_widget(btn_voltar)
        root.add_widget(row)
        self.add_widget(root)

    def voltar(self, *_):
        self.manager.current = "home"

    def corrigir(self, *_):
        try:
            core.PASTA_RESULTADO.mkdir(parents=True, exist_ok=True)
            imagens = core.listar_imagens(core.PASTA_RESULTADO)
            if not imagens:
                raise ValueError("Sem imagens na pasta resultado.")

            resultados = []
            for arq in imagens:
                try:
                    payload = ""
                    try:
                        payload = core.ler_qr_de_imagem(arq)
                    except Exception:
                        payload = ""

                    config_base = core.carregar_config_para_caminho(core.PASTA_RESULTADO)
                    if payload:
                        try:
                            dados = core.extrair_dados_qr(payload)
                            r = core.corrigir(config_base, dados)
                            resultados.append(
                                {
                                    "arquivo": arq.name,
                                    "status": "ok",
                                    "aluno_id": r["aluno_id"],
                                    "nome_aluno": self.nome.text.strip(),
                                    "turma": self.turma.text.strip(),
                                    "serie": self.serie.text.strip(),
                                    "prova_id": r["prova_id"],
                                    "acertos": r["acertos"],
                                    "qtd_questoes": r["qtd_questoes"],
                                    "nota": r["nota"],
                                    "nota_maxima": r["nota_maxima"],
                                    "respostas_lidas": dados.get("respostas", ""),
                                    "erro": "",
                                }
                            )
                            continue
                        except Exception:
                            pass

                    cfg = core.config_por_qr_oficial(payload) if payload else None
                    if not cfg:
                        cfg = config_base
                    resp = core.extrair_respostas_marcadas_da_folha(arq, int(cfg["qtd_questoes"]))
                    if not resp or set(resp) <= {"-"}:
                        raise ValueError("Nao foi possivel ler as marcacoes.")
                    r = core.corrigir(
                        cfg,
                        {
                            "aluno_id": core.inferir_aluno_id_por_nome(arq),
                            "prova_id": str(cfg["prova_id"]),
                            "respostas": resp,
                        },
                    )
                    resultados.append(
                        {
                            "arquivo": arq.name,
                            "status": "ok",
                            "aluno_id": r["aluno_id"],
                            "nome_aluno": self.nome.text.strip(),
                            "turma": self.turma.text.strip(),
                            "serie": self.serie.text.strip(),
                            "prova_id": r["prova_id"],
                            "acertos": r["acertos"],
                            "qtd_questoes": r["qtd_questoes"],
                            "nota": r["nota"],
                            "nota_maxima": r["nota_maxima"],
                            "respostas_lidas": resp,
                            "erro": "",
                        }
                    )
                except Exception as e:
                    resultados.append(
                        {
                            "arquivo": arq.name,
                            "status": "erro",
                            "aluno_id": "",
                            "nome_aluno": self.nome.text.strip(),
                            "turma": self.turma.text.strip(),
                            "serie": self.serie.text.strip(),
                            "prova_id": "",
                            "acertos": "",
                            "qtd_questoes": "",
                            "nota": "",
                            "nota_maxima": "",
                            "respostas_lidas": "",
                            "erro": str(e),
                        }
                    )

            saida = core.PASTA_RESULTADO / "resultado_mobile.pdf"
            core.salvar_relatorio_pdf_resultado(resultados, saida)
            ok = sum(1 for r in resultados if r.get("status") == "ok")
            show_message("Concluido", f"Processadas: {len(resultados)}\nSucesso: {ok}\nPDF: {saida}")
        except Exception as e:
            show_message("Erro", str(e))


class MobileApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ConfigScreen(name="config"))
        sm.add_widget(FolhaScreen(name="folha"))
        sm.add_widget(CorrecaoScreen(name="correcao"))
        return sm


if __name__ == "__main__":
    MobileApp().run()
