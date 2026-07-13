# Tree Geometry Estimator for Outdoor Lighting Models

!!! tip "Calculadora interativa"
    Experimente a **[calculadora interativa](app/index.html)** — roda inteiramente no navegador, sem envio de dados.


**Estimativa preliminar de altura, diâmetro do dossel e parâmetros geométricos
de árvores para modelos luminotécnicos externos.**

!!! warning "Ressalva metodológica"
    Os resultados representam **estimativas preliminares** destinadas à
    pré-modelagem luminotécnica. A ferramenta **não substitui** levantamento
    dendrométrico, medição de campo, inventário florestal, laudo arborístico,
    avaliação de estabilidade ou levantamento topográfico. Os parâmetros não
    foram calibrados localmente; os intervalos são **cenários de sensibilidade**,
    não intervalos estatísticos de confiança. Copas reais podem ser assimétricas;
    poda e condições urbanas alteram a geometria; palmeiras têm maior incerteza;
    árvores próximas a luminárias devem ser medidas em campo.

<div class="hero-buttons" markdown>
[Metodologia](methodology-page.md){ .md-button }
[Demonstração](demo.md){ .md-button }
[Repositório :simple-github:](https://github.com/czanchetta/urban-tree-geometry){ .md-button .md-button--primary }
</div>

## Resumo

A partir de um inventário mínimo — identificador, espécie e **perímetro do
tronco** — a ferramenta calcula DAP, altura estimada, diâmetro do dossel e os
parâmetros X, Y e Z para modelagem 3D preliminar de árvores no DIALux.

<figure markdown>
  ![Fluxo de cálculo](assets/workflow.svg)
  <figcaption>Fluxo de cálculo, com a proveniência de cada valor
  (medido, derivado, adotado, heurístico).</figcaption>
</figure>

## Exemplo de resultado

<figure markdown>
  ![Altura versus DAP](assets/height_vs_dap.png)
  <figcaption>Modelo assintótico de altura por classe de porte adotada.</figcaption>
</figure>

O núcleo de altura reproduz fielmente a planilha de origem (62/62 linhas
idênticas). A camada de dossel/DIALux é uma **heurística** de engenharia,
claramente identificada e não validada contra a planilha.
